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

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return {"message": "StockBot API is running."}



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

@app.api_route("/update-daily", methods=["GET", "POST", "HEAD"])
def update_daily():
    """
    Runs the daily update logic (same as daily.py):
    - Fetches latest SPY data from Alpha Vantage
    - Updates the previous day's Target
    - Appends new row
    - Generates features
    - Makes new prediction
    - Updates stats.json
    - Saves everything
    Returns success status and new prediction info.
    """
    try:
        # Re-import here to avoid loading at startup (in case env changes)
        from alpha_vantage.timeseries import TimeSeries
        import os
        from dotenv import load_dotenv
        load_dotenv()

        API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
        if not API_KEY:
            return {"error": "Alpha Vantage API key not found in environment"}

        threshold = 0.6
        predictors = ['Close_Ratio_2', 'Trend_2', 'Close_Ratio_5', 'Trend_5', 'Close_Ratio_20',
                      'Trend_20', 'Close_Ratio_60', 'Trend_60', 'Close_Ratio_250', 'Trend_250']

        # Load current data and stats
        df = pd.read_parquet("data.parquet")

        stats = load_json()

        # Fetch latest market data
        ts = TimeSeries(key=API_KEY, output_format='pandas')
        data, meta = ts.get_daily(symbol="SPY", outputsize="compact")

        # Get the most recent trading day
        latest_day_raw = data.iloc[0]
        latest_date = latest_day_raw.name.date()  # Alpha Vantage returns Timestamp index

        # Check if we already have this day
        if latest_date in df.index.date:
            return {
                "status": "no_update",
                "message": f"Data for {latest_date} already exists. Nothing to do.",
                "latest_date_in_db": df.index[-1].strftime("%Y-%m-%d")
            }

        # Format latest day properly
        latest_day = latest_day_raw[:-1].copy()  # Drop volume
        latest_day.index = ["Open", "High", "Low", "Close"]  # Fix typo if any

        # === UPDATE PREVIOUS DAY'S TARGET ===
        previous_day_close = df.iloc[-1]["Close"]
        today_close = latest_day["Close"]

        df.at[df.index[-1], "Tomorrow"] = today_close
        df.at[df.index[-1], "Target"] = int(today_close > previous_day_close)

        # === APPEND NEW ROW ===
        new_row = latest_day.to_frame().T
        new_row.index = [pd.Timestamp(latest_date)]  # Ensure index is datetime
        df = pd.concat([df, new_row])

        # === FEATURE ENGINEERING FOR NEW ROW ===
        horizons = [2, 5, 20, 60, 250]
        for horizon in horizons:
            # Trend: number of up days in last `horizon` trading days (excluding today)
            rolling_targets = df["Target"].iloc[-(horizon + 1):-1]
            df.at[df.index[-1], f"Trend_{horizon}"] = rolling_targets.sum()

            # Close ratio: today's close / average close over last `horizon` days
            df.at[df.index[-1], f"Close_Ratio_{horizon}"] = (
                df["Close"].iloc[-1] / df["Close"].iloc[-horizon:-1].mean()
            )

        # === MAKE PREDICTION ===
        model = joblib.load("model.pkl")
        X_new = df[predictors].iloc[-1:].copy()
        pred_prob = model.predict_proba(X_new)[0, 1]
        signal = int(pred_prob > threshold)

        # === UPDATE STATS IF WE HAD A PREVIOUS BUY SIGNAL ===
        if stats["last_prediction"] == 1:
            stats["total_buys"] += 1
            if df.iloc[-2]["Target"] == 1:  # Yesterday's actual target
                stats["correct_buys"] += 1

        # Update last prediction
        stats["last_prediction"] = signal

        # === SAVE EVERYTHING ===
        df.to_parquet("data.parquet")
        with open("stats.json", "w") as f:
            json.dump(stats, f, indent=4)

        # === RETURN RESPONSE ===
        return {
            "status": "success",
            "updated_date": latest_date.strftime("%Y-%m-%d"),
            "new_close": float(today_close),
            "prediction_probability": float(pred_prob),
            "buy_signal": bool(signal),
            "total_buys": stats["total_buys"],
            "correct_buys": stats["correct_buys"],
            "win_rate": (
                stats["correct_buys"] / stats["total_buys"] 
                if stats["total_buys"] > 0 else 0
            )
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}