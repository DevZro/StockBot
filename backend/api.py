import pandas as pd
import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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

# Load model once at startup (efficient)
model = joblib.load("model.pkl")

# Load the dataset
def load_data():
    return pd.read_parquet("data.parquet")

predictors = [
    'Close_Ratio_2', 'Trend_2',
    'Close_Ratio_5', 'Trend_5',
    'Close_Ratio_20', 'Trend_20',
    'Close_Ratio_60', 'Trend_60',
    'Close_Ratio_250', 'Trend_250'
]

threshold = 0.675 


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

    
    # Last 30 days
    last_30 = df.tail(30)
    
    dates = [d.strftime("%Y-%m-%d") for d in last_30.index]
    close = last_30["Close"].tolist()
    
    latest = df.iloc[-1]
    
    # Example statistics (replace with your actual logic)
    total_buys = 0
    correct_buys = 0
    win_percent = 0
    
    # Make input 2D for sklearn
    X = (latest.to_frame().T)[predictors]

    # Prediction probability for class 1
    pred_prob = model.predict_proba(X)[0, 1]
    signal = bool(pred_prob > threshold)

    next_market_day = (latest.name + pd.tseries.offsets.BDay(1)).strftime("%Y-%m-%d")  
    
    return {
        "total_buys": total_buys,
        "correct_buys": correct_buys,
        "win_percent": win_percent,
        "next_date": next_market_day,
        "buy_signal": True,
        "last_month_dates": dates,
        "last_month_close": close
    }



@app.get("/predict")
def predict():
    """
    Returns the model's prediction probability
    and buy/no-buy signal.
    """
    df = load_data()
    latest = df.iloc[-1]

    # Make input 2D for sklearn
    X = (latest.to_frame().T)[predictors]

    # Prediction probability for class 1
    pred_prob = model.predict_proba(X)[0, 1]
    signal = "BUY" if pred_prob > threshold else "NO BUY"

    return {
        "prediction_probability": pred_prob,
        "signal": signal
    }
