import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from portfolio_engine import TickerData, OptionsSnapshot, analyze_ticker, SetupDecision

# --- CONFIG ---
# (Ideally import from config.py)
FMP_API_KEY = os.getenv('FMP_API_KEY')
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY')

# Defines the universe to scan. 
# Expanded universe to ensure tabs are populated with WATCH candidates.
MASTER_TICKER_LIST = [
    # Mega Cap / Tech Leaders
    "TSLA", "NVDA", "AMD", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "AVGO",
    # Growth / Momentum
    "PLTR", "SOFI", "DKNG", "HOOD", "RIVN", "CVNA", "UPST", "AFRM", "COIN", "MARA",
    "NET", "DDOG", "SNOW", "CRWD", "ZS", "PANW", "TTD", "ROKU", "SHOP", "SE",
    # Financials
    "JPM", "BAC", "WFC", "GS", "C", "MS", "BLK", "AXP", "V", "MA", "PYPL",
    # Industrial / Energy / Classic
    "CAT", "DE", "BA", "LMT", "XOM", "CVX", "COP", "SLB", "HAL", "OXY",
    # Consumer / Retail
    "MCD", "SBUX", "NKE", "LULU", "TGT", "WMT", "COST", "HD", "LOW", "CMG",
    # Pharma / Bio
    "LLY", "NVO", "MRK", "JNJ", "PFE", "ABBV", "AMGN", "GILD", "VRTX", "REGN",
    # ETFs (for Options / Ref)
    "SPY", "QQQ", "IWM", "DIA", "TLT", "SMH", "XLF", "XLE", "XLK", "ARKK",
    # Meme / High Vol
    "GME", "AMC"
]

def fetch_ticker_data_triple_api(symbol: str) -> Optional[TickerData]:
    """
    Fetch data using Triple API Fallback: FMP -> Twelve Data -> Yahoo
    Returns TickerData object with computed technicals.
    """
    df = None
    
    # 1. Try FMP
    if FMP_API_KEY:
        try:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_API_KEY}"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if "historical" in data:
                df = pd.DataFrame(data["historical"])
                df = df.iloc[::-1].reset_index(drop=True) # Oldest first
                df.rename(columns={"date":"Date", "open":"Open", "high":"High", "low":"Low", "close":"Close", "volume":"Volume"}, inplace=True)
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
        except Exception as e:
            print(f"FMP failed for {symbol}: {e}")

    # 2. Try Twelve Data
    if df is None and TWELVE_DATA_API_KEY:
        try:
            url = "https://api.twelvedata.com/time_series"
            params = {"symbol": symbol, "interval": "1day", "outputsize": 365, "apikey": TWELVE_DATA_API_KEY, "order": "ASC"}
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            if "values" in data:
                df = pd.DataFrame(data["values"])
                df.rename(columns={"datetime": "Date", "open":"Open", "high":"High", "low":"Low", "close":"Close", "volume":"Volume"}, inplace=True)
                for col in ["Open", "High", "Low", "Close", "Volume"]: df[col] = pd.to_numeric(df[col])
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
        except Exception as e:
            print(f"Twelve Data failed for {symbol}: {e}")

    # 3. Try Yahoo Finance
    if df is None:
        try:
            df = yf.download(symbol, period="2y", progress=False)
            if df.empty: return None
            # Handle MultiIndex if needed (though single ticker usually doesn't return multiindex columns properly in new yf versions sometimes)
            if isinstance(df.columns, pd.MultiIndex):
                df = df.xs(symbol, axis=1, level=1)
        except Exception as e:
            print(f"Yahoo failed for {symbol}: {e}")
            return None

    if df is None or df.empty:
        return None

    # Calculate indicators
    close = df['Close']
    
    # Basics
    price = float(close.iloc[-1])
    try:
        prev_close = float(close.iloc[-2])
    except IndexError:
        prev_close = price # Fallback for very new stocks
        
    change_pct = ((price - prev_close) / prev_close) * 100
    
    # Moving Averages
    sma50 = close.rolling(window=50).mean().iloc[-1]
    sma200 = close.rolling(window=200).mean().iloc[-1]
    
    ema9 = close.ewm(span=9, adjust=False).mean().iloc[-1]
    ema21 = close.ewm(span=21, adjust=False).mean().iloc[-1]
    
    # Volume
    volume = float(df['Volume'].iloc[-1])
    avg_vol_20 = df['Volume'].rolling(window=20).mean().iloc[-1]
    avg_vol_50 = df['Volume'].rolling(window=50).mean().iloc[-1]
    
    # Recent Highs/Lows (20 days)
    recent_high_20 = df['High'].rolling(window=20).max().iloc[-1]
    recent_low_20 = df['Low'].rolling(window=20).min().iloc[-1]
    
    # Gap
    open_price = float(df['Open'].iloc[-1])
    gap_pct_today = (open_price - prev_close) / prev_close
    
    # Simple RS Trend logic (Proxy: Is it above SMA50?)
    if price > sma50 and sma50 > sma200:
        rs_trend = "rising"
    elif price < sma50 and price < sma200:
        rs_trend = "falling"
    else:
        rs_trend = "flat"

    return TickerData(
        symbol=symbol,
        price=price,
        high=float(df['High'].iloc[-1]),
        low=float(df['Low'].iloc[-1]),
        open=open_price,
        close=price,
        prevClose=prev_close,
        changePct=change_pct,
        volume=volume,
        avgVol20=avg_vol_20,
        avgVol50=avg_vol_50,
        sma50=sma50,
        sma200=sma200,
        ema9=ema9,
        ema21=ema21,
        rsTrend=rs_trend,
        recentHigh20=recent_high_20,
        recentLow20=recent_low_20,
        gapPctToday=gap_pct_today,
        daysToEarnings=None # Placeholder
    )

def fetch_options_snapshot(symbol: str) -> OptionsSnapshot:
    # Basic options check using yfinance (simplified as real options data is hard to scrape reliably without paid API)
    try:
        t = yf.Ticker(symbol)
        if not t.options:
             return OptionsSnapshot(hasOptions=False)
             
        # Just return generic "Good" options data for now to test logic
        # In production this requires heavy lifting or paid endpoint
        return OptionsSnapshot(
            hasOptions=True,
            spreadPct=0.02, # 2% spread (Good)
            openInterest=5000,
            totalVolume=10000
        )
    except:
        return OptionsSnapshot(hasOptions=False)

def get_portfolio_data() -> Dict[int, List[SetupDecision]]:
    """
    Main entry point suitable for main.py
    Scans master list -> Runs Logic -> buckets into accounts
    """
    decisions = []
    
    for ticker in MASTER_TICKER_LIST:
        td = fetch_ticker_data_triple_api(ticker)
        if not td: continue
        
        opt = fetch_options_snapshot(ticker)
        
        decision = analyze_ticker(td, opt)
        decisions.append(decision)
        
    # Bucket by account
    buckets = {i: [] for i in range(9)} # 0-8
    
    for d in decisions:
        buckets[d.accountId].append(d)
        
    # Sort buckets by score
    for i in buckets:
        buckets[i].sort(key=lambda x: x.score, reverse=True)
        
    return buckets
