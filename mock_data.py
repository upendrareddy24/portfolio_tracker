import random
from datetime import datetime, timedelta

TICKERS = ["AAPL", "NVDA", "TSLA", "AMD", "PLTR", "AMZN", "MSFT", "GOOGL", "META", "NFLX"]

def generate_mock_tickers(count=5):
    tickers_data = []
    for _ in range(count):
        symbol = random.choice(TICKERS)
        price = round(random.uniform(100, 1000), 2)
        change_pct = round(random.uniform(-5, 5), 2)
        entry_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        tickers_data.append({
            "symbol": symbol,
            "price": price,
            "change": change_pct,
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "days_held": (datetime.now() - entry_date).days
        })
    return tickers_data
