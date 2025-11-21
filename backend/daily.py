import pandas as pd
import numpy as np
import joblib
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, time, timezone
import os
from dotenv import load_dotenv

load_dotenv()

threshold = 0.675
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")

now = datetime.now(timezone.utc)  # Current time in GMT
weekday = now.weekday()            # 0 = Monday, 6 = Sunday

# Market closes at 21:00 GMT plus buffer so 23:00 GMT
market_close = time(23, 0)        

if weekday >= 5:  # Saturday=5, Sunday=6
    print("Market closed on weekend. Exiting.")
    exit()

"""if now.time() < market_close:
    print("Market has not closed yet. Exiting.")
    exit()"""

# Load existing historical data
df = pd.read_parquet("data.parquet")

# Get the data of the latest day from alpha_vantage
ts = TimeSeries(key=API_KEY, output_format='pandas')
data, meta = ts.get_daily(symbol="SPY", outputsize="compact")

# Make compatible with current format
latest_day = data.iloc[0][:-1]
latest_day.index = ["Open", "High", "Low", "Close"]

# Change previous day target from nan to 1/0
df.at[df.index[-1], "Tomorrow"] = latest_day["Close"].item()
df.at[df.index[-1], "Target"] = int(latest_day["Close"].item() > df.at[df.index[-1], "Close"])

# Add to existing df
df = pd.concat([df, latest_day.to_frame().T])


horizons = [2, 5, 20, 60, 250]
for horizon in horizons:
    df.at[df.index[-1], f"Trend_{horizon}"] = df["Target"].iloc[-1*(horizon + 1) : -1].sum()
    df.at[df.index[-1], f"Close_Ratio_{horizon}"] = df["Close"].iloc[-1] / df["Close"].iloc[-1*horizon : ].mean()


# Upload updated df
df.to_parquet("data.parquet")
