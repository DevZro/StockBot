import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
import joblib

df = pd.read_parquet("data.parquet")
df = df.dropna()

predictors = ['Close_Ratio_2', 'Trend_2', 'Close_Ratio_5', 'Trend_5', 'Close_Ratio_20', 
              'Trend_20', 'Close_Ratio_60', 'Trend_60', 'Close_Ratio_250', 'Trend_250']

model = RandomForestClassifier(n_estimators=50, min_samples_split=50, random_state=42)

model.fit(df[predictors], df["Target"])

joblib.dump(model, 'model.pkl', compress=3)