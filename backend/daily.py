import pandas as pd
import numpy as np
import joblib
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, time, timezone
import os
import json
from dotenv import load_dotenv

load_dotenv()

threshold = 0.6
predictors = ['Close_Ratio_2', 'Trend_2', 'Close_Ratio_5', 'Trend_5', 'Close_Ratio_20', 
              'Trend_20', 'Close_Ratio_60', 'Trend_60', 'Close_Ratio_250', 'Trend_250']
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")      

# Load existing historical data
df = pd.read_parquet("data.parquet")

with open("stats.json", "r") as file:
    stats = json.load(file)

# Get the data of the latest day from alpha_vantage
ts = TimeSeries(key=API_KEY, output_format='pandas')
data, meta = ts.get_daily(symbol="SPY", outputsize="compact")

for i in range(1, -1, -1):
    # Make compatible with current format
    latest_day = data.iloc[i][:-1]
    latest_day.index = ["Open", "High", "Low", "Close"]

    if latest_day.name == df.iloc[-1].name:
        print("Market Day already recorded.")
        exit()

    # Change previous day target from nan to 1/0
    df.at[df.index[-1], "Tomorrow"] = latest_day["Close"].item()
    df.at[df.index[-1], "Target"] = int(latest_day["Close"].item() > df.at[df.index[-1], "Close"])

    # Add to existing df
    df = pd.concat([df, latest_day.to_frame().T])


    horizons = [2, 5, 20, 60, 250]
    for horizon in horizons:
        df.at[df.index[-1], f"Trend_{horizon}"] = df["Target"].iloc[-1*(horizon + 1) : -1].sum()
        df.at[df.index[-1], f"Close_Ratio_{horizon}"] = df["Close"].iloc[-1] / df["Close"].iloc[-1*horizon : ].mean()

    model = joblib.load("model.pkl")

    X = (df.iloc[-1].to_frame().T)[predictors]
    pred_prob = model.predict_proba(X)[0, 1]
    signal = int(bool(pred_prob > threshold))

    if stats["last_prediction"] == 1:
        stats["total_buys"] += 1
        if df.iloc[-1]["Target"] == 1:
            stats["correct_buys"] += 1
        
    stats["last_prediction"] = signal

    stats["dates"] = df.index.strftime("%Y-%m-%d").tolist()[-30:]

with open("stats.json", "w") as f:
    stats = json.dump(stats, f, indent=4)

# Upload updated df
df.to_parquet("data.parquet")