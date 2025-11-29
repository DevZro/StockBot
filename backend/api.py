import pandas as pd
import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()


origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] for all origins during testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load the dataset
def load_data():
    return pd.read_parquet("data.parquet")

def load_json():
    with open("stats.json", "r") as file:
        stats = json.load(file)
    return stats

@app.get("/")
def home():
    return {"status": "API is running"}



@app.get("/latest")
def get_latest_row():
    """
    Returns the latest row of your dataset
    for frontend display.
    """
    df = load_data()

    stats = load_json()

    # Last 30 days
    last_30 = df.tail(30)
    
    dates = [d.strftime("%Y-%m-%d") for d in last_30.index]
    close = last_30["Close"].tolist()
    
    latest = df.iloc[-1]
    
    # Example statistics (replace with your actual logic)
    total_buys = stats["total_buys"]
    correct_buys = stats["correct_buys"]
    try:
        win_percent = correct_buys / total_buys
    except ZeroDivisionError: # takes care of 0/0 case
        win_percent = 0
    signal = stats["last_prediction"] 


    next_market_day = (latest.name + pd.tseries.offsets.BDay(1)).strftime("%Y-%m-%d")  
    
    return {
        "total_buys": total_buys,
        "correct_buys": correct_buys,
        "win_percent": win_percent,
        "next_date": next_market_day,
        "buy_signal": signal,
        "last_month_dates": dates,
        "last_month_close": close
    }
