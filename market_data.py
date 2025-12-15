import yfinance as yf
import random
from typing import List, Dict, Any

# Predefined tickers mapping to strategy types for demonstration
# In the future, this can be replaced by the complex "book-based" selection logic
STRATEGY_TICKERS = {
    "SH Swing": ["TSLA", "NVDA", "AMD", "MARA", "COIN"], # High beta/volatility
    "Swing/Sq": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"], # Mega cap tech
    "POS- BO/SQ": ["PLTR", "SOFI", "DKNG", "HOOD", "RIVN"], # Growth/Breakout candidates
    "POS-HVOL": ["GME", "AMC", "CVNA", "UPST", "AFRM"], # High Volume/Meme
    "POS-PAT": ["JPM", "BAC", "WFC", "GS", "C"], # Patterns/Financials
    "INV": ["KO", "PEP", "JNJ", "PG", "MCD"], # Long term/Value
    "OPT-Swing": ["SPY", "QQQ", "IWM", "DIA", "TLT"], # ETFs for options
    "Lot": ["INTC", "F", "T", "VZ", "PFE"], # Lotto/Cheap
    "Reference": ["^GSPC", "^DJI", "^IXIC", "BTC-USD", "GC=F"] # Market Indicies
}

def get_tickers_for_strategy(strategy: str) -> List[Dict[str, Any]]:
    """
    Fetches real-time data for tickers associated with a given strategy.
    Designed to be easily swapped with FMP or other APIs later.
    """
    symbols = STRATEGY_TICKERS.get(strategy, ["SPY", "AAPL", "MSFT"]) # Default fallback
    
    # Randomly select a subset to keep it looking dynamic but consistent
    # In production, this would be the user's actual holdings
    selected_symbols = symbols 

    try:
        # Batch fetch for performance
        data = yf.download(selected_symbols, period="5d", progress=False)
        
        results = []
        for symbol in selected_symbols:
            try:
                # Extract latest close and previous close
                # yfinance returns a MultiIndex DataFrame if multiple tickers
                if len(selected_symbols) > 1:
                   current_price = data['Close'][symbol].iloc[-1]
                   prev_close = data['Close'][symbol].iloc[-2]
                else:
                   current_price = data['Close'].iloc[-1]
                   prev_close = data['Close'].iloc[-2]

                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                
                # Mocking "days held" as that is user-portfolio specific, not market data
                days_held = random.randint(1, 45) 

                results.append({
                    "symbol": symbol,
                    "price": round(float(current_price), 2),
                    "change": round(float(change_pct), 2),
                    "entry_date": "N/A", # Placeholder until DB
                    "days_held": days_held
                })
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                # Fallback implementation for errors
                results.append({
                    "symbol": symbol,
                    "price": 0.00,
                    "change": 0.00,
                    "entry_date": "Error",
                    "days_held": 0
                })
        
        return results

    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
