from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv
import os


load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")


ts = TimeSeries(key=API_KEY, output_format='pandas')
data, meta = ts.get_daily(symbol="SPY", outputsize="full")

data = data.iloc[::-1]
del data['5. volume']

data.columns = ["Open", "High", "Low", "Close"]

data["Tomorrow"] = data["Close"].shift(-1)
data["Target"] = (data["Tomorrow"] > data["Close"]).astype(int)
data.head()

horizons = [2, 5, 20, 60, 250]
predictors = []

for horizon in horizons:
    data[f"Close_Ratio_{horizon}"] = data["Close"] / data.rolling(horizon).mean()["Close"]
    data[f"Trend_{horizon}"] = data.shift(1).rolling(horizon).sum()["Target"]

    predictors += [f"Close_Ratio_{horizon}", f"Trend_{horizon}"]

data = data.dropna()
data.to_parquet("data.parquet")

