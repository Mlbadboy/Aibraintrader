import requests
import feedparser
import logging
import urllib.parse
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

class SentimentEngine:
    """
    Engine for fetching news and calculating sentiment score using VADER NLP.
    """
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_yahoo_headlines(self, symbol: str) -> list:
        """
        Scrapes recent headlines from Yahoo Finance.
        """
        headlines = []
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for h3 in soup.find_all("h3"):
                    if h3.text:
                        headlines.append(h3.text)
            return headlines[:10]
        except Exception as e:
            logger.warning(f"[SentimentEngine] Failed fetching Yahoo headlines for {symbol}: {e}")
            return []

    def fetch_google_news_rss(self, symbol: str) -> list:
        """
        Fetches news from Google News RSS feed.
        """
        headlines = []
        try:
            # clean symbol for search
            clean_sym = symbol.split('.')[0].replace('=', '').replace('X', '')
            query = urllib.parse.quote(f"{clean_sym} stock news")
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            # Use requests with timeout to prevent feedparser from hanging indefinitely
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:10]:
                    headlines.append(entry.title)
            return headlines
        except Exception as e:
            logger.warning(f"[SentimentEngine] Failed fetching Google RSS for {symbol}: {e}")
            return []

    def score_text(self, text: str) -> float:
        """
        Returns a sentiment score normalized between 0.0 (Bearish) and 1.0 (Bullish).
        VADER 'compound' score ranges from -1 to 1. We map it to 0-1.
        """
        try:
            vs = self.analyzer.polarity_scores(text)
            compound = vs['compound']
            # Map -1 to 1 into 0 to 1
            normalized = (compound + 1) / 2
            return normalized
        except Exception as e:
            logger.error(f"[SentimentEngine] VADER analysis failed on text: {e}")
            return 0.5

    def analyze_sentiment(self, symbol: str) -> dict:
        """
        Main entry point for Sentiment Agent.
        """
        logger.info(f"[SentimentEngine] Analyzing sentiment for {symbol}")
        
        # Aggregate headlines from multiple sources
        headlines = self.fetch_yahoo_headlines(symbol)
        if len(headlines) < 5:
            headlines.extend(self.fetch_google_news_rss(symbol))
            
        # Deduplicate
        headlines = list(set(headlines))
        
        if not headlines:
            return {"score": 0.5, "status": "no_data", "headlines_analyzed": 0}
            
        scores = [self.score_text(hl) for hl in headlines]
        avg_score = sum(scores) / len(scores)
        
        return {
            "score": round(avg_score, 3),
            "status": "success",
            "headlines_analyzed": len(headlines)
        }

if __name__ == "__main__":
    engine = SentimentEngine()
    print("Testing Sentiment Engine (NVDA):")
    res = engine.analyze_sentiment("NVDA")
    print(res)
