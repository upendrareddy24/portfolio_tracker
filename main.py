from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from config import ACCOUNTS, get_account_by_id
from market_data import get_portfolio_data

import os
from datetime import datetime

app = FastAPI()

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    print("Warning: 'static' directory not found. Static files will not be served.")
templates = Jinja2Templates(directory="templates")

# Cache mechanism (Basic)
CACHE = {
    "data": {},
    "timestamp": 0
}
CACHE_DURATION = 300 # 5 minutes

@app.get("/")
async def read_root(request: Request, account_id: int = 1):
    
    import time
    now = time.time()
    
    # Check cache (simplified for multi-account structure)
    if not CACHE["data"] or (now - CACHE["timestamp"] > CACHE_DURATION):
        print("Refreshing Portfolio Logic Data...")
        CACHE["data"] = get_portfolio_data()
        CACHE["timestamp"] = now
        
    portfolio_buckets = CACHE["data"]
    
    # Get current account config
    current_account = get_account_by_id(account_id)
    
    # Get tickers for this account logic
    # buckets is {1: [Decision, ...], 2: [...]}
    tickers = portfolio_buckets.get(account_id, [])
    
    # Calculate summary stats (optional)
    total_tickers = len(tickers)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "accounts": ACCOUNTS,
        "current_account": current_account,
        "tickers": tickers,
        "last_updated": datetime.fromtimestamp(CACHE["timestamp"]).strftime('%H:%M:%S')
    })
