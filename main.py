from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
import random

from config import ACCOUNTS, get_account_by_id
from market_data import get_tickers_for_strategy

app = FastAPI(title="Portfolio Tracker")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass # Static dir might not exist yet

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, account_id: int = 1):
    current_account = get_account_by_id(account_id)
    
    # Fetch real data based on the account's strategy
    tickers = get_tickers_for_strategy(current_account["strategy"])
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "title": "Portfolio Tracker",
        "accounts": ACCOUNTS,
        "current_account": current_account,
        "tickers": tickers
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
