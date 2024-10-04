from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# Function to fetch news from the database
def get_news():
    conn = sqlite3.connect('wolf_trader.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, sentiment, recommendation, link FROM financial_news")
    news_list = cursor.fetchall()
    conn.close()
    
    return [{'title': row[0], 'sentiment': row[1], 'recommendation': row[2], 'link': row[3]} for row in news_list]

@app.route('/')
def dashboard():
    news = get_news()
    return render_template('dashboard.html', news=news)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
