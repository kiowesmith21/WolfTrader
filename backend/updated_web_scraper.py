import sqlite3
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from alpha_vantage.timeseries import TimeSeries
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch Alpha Vantage API key from environment variables
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Function to get stock data from Alpha Vantage
def get_stock_data(symbol):
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
    try:
        data, meta_data = ts.get_quote_endpoint(symbol=symbol)
        return data
    except Exception as e:
        print(f"Failed to retrieve stock data: {e}")
        return None

# Create database and table
def create_db():
    conn = sqlite3.connect('wolf_trader.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS financial_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT,
        sentiment TEXT,
        sentiment_score REAL,
        recommendation TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

# Initialize the database
create_db()

# Function to scrape financial news from Yahoo Finance
def scrape_yahoo_finance():
    url = 'https://finance.yahoo.com/'
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find headlines (Yahoo Finance)
    headlines = soup.find_all('h3', class_='clamp tw-line-clamp-none yf-1sxfjua')
    print(f"Found {len(headlines)} headlines")  # Print number of headlines found
    news_list = []
    
    if not headlines:
        print("No headlines found. The structure of the page might have changed.")
        return []

    for headline in headlines:
        title = headline.text.strip()
        link_tag = headline.find('a')
        link = link_tag['href'] if link_tag else None
        
        # Ensure the link is fully qualified
        if link:
            full_link = f"https://finance.yahoo.com{link}" if not link.startswith('http') else link
        else:
            full_link = 'No link available'

        # Append title and link to the news_list
        news_list.append({'title': title, 'link': full_link})

    return news_list


# Function to analyze sentiment of each headline
def analyze_sentiment(news_list):
    for news in news_list:
        # Perform sentiment analysis on the headline
        analysis = TextBlob(news['title'])
        sentiment_score = analysis.sentiment.polarity  # Sentiment polarity: -1 (negative), 0 (neutral), 1 (positive)
        
        # Classify based on polarity
        if sentiment_score > 0:
            sentiment = "Positive"
        elif sentiment_score < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        
        # Add sentiment info and recommendation to the news item
        news['sentiment'] = sentiment
        news['sentiment_score'] = sentiment_score
        news['recommendation'] = generate_trade_recommendation(sentiment_score)
    
    return news_list

# Function to generate trade recommendation
def generate_trade_recommendation(sentiment_score):
    if sentiment_score > 0:
        return "Buy"
    elif sentiment_score < 0:
        return "Sell"
    else:
        return "Hold"

# Function to insert news data into the SQLite database
def insert_news_data(news_list):
    conn = sqlite3.connect('wolf_trader.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS financial_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        link TEXT NOT NULL,
        sentiment TEXT,
        sentiment_score REAL,
        recommendation TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    for news in news_list:
        cursor.execute('SELECT * FROM financial_news WHERE title = ? AND link = ?', (news['title'], news['link']))
        if cursor.fetchone() is None:
            cursor.execute('''
            INSERT INTO financial_news (title, link, sentiment, sentiment_score, recommendation)
            VALUES (?, ?, ?, ?, ?)
            ''', (news['title'], news['link'], news['sentiment'], news['sentiment_score'], news['recommendation']))


    conn.commit()
    conn.close()

# Main function to scrape, analyze, and insert data
def main():
    financial_news = scrape_yahoo_finance()

    if financial_news:
        analyzed_news = analyze_sentiment(financial_news)
        insert_news_data(analyzed_news)

        for index, news in enumerate(analyzed_news):
            print(f"{index + 1}. {news['title']}")
            print(f"Sentiment: {news['sentiment']} (Score: {news['sentiment_score']})")
            print(f"Link: {news['link']}")
            print(f"Trade Recommendation: {news['recommendation']}")
    else:
        print("No news data found.")

    # Example: Fetch stock data for Apple (AAPL)
    stock_data = get_stock_data('AAPL')
    if stock_data:
        print(f"Apple Stock Data: {stock_data}")

# Run the main function
if __name__ == "__main__":
    main()
