import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score

df = pd.read_parquet("data.parquet")
df = df.dropna() # drops the final day which has no target value yet
predictors = ['Close_Ratio_2', 'Trend_2', 'Close_Ratio_5', 'Trend_5', 'Close_Ratio_20', 
              'Trend_20', 'Close_Ratio_60', 'Trend_60', 'Close_Ratio_250', 'Trend_250']

def predict(train, test, predictors, model_class, model_params, thresholds):
    all_preds = []
    model = model_class(**model_params)
    model.fit(train[predictors], train["Target"])
    preds = model.predict_proba(test[predictors])[:,1]
    for i in range(len(thresholds)):
        all_preds.append((preds >= thresholds[i]).astype(int))
    all_preds.append(test["Target"].values)
    return all_preds

def backtest(data, model_class, model_params, predictors, thresholds, start=2500, step=250):
    all_predictions = []

    for i in range(start, data.shape[0], step):
        preds = predict(data.iloc[0 : i], data.iloc[i : i + 250], predictors, model_class, model_params, thresholds)
        all_predictions.append(preds)
 
    result = [np.concatenate(arrs) for arrs in zip(*all_predictions)]
    return result

thresholds=[i * 0.025 for i in range(29)]
n_estimators_list = [50, 100, 200]
min_samples_split_list = [20, 50, 100]

gridSearch = pd.DataFrame()
percentBuys = pd.DataFrame()
model_class = RandomForestClassifier

for n_estimators in n_estimators_list:
    for min_samples_split in min_samples_split_list:
        model_params = {"n_estimators" : n_estimators, "min_samples_split" : min_samples_split, "random_state" : 42}
        
        results = backtest(df, model_class, model_params, predictors, thresholds)
        
        scores = []
        percent_buys = []
        for i in range(len(results) - 1):
            scores.append(precision_score(results[-1], results[i]))
            percent_buys.append(np.sum(results[i]) / results[i].shape[0])
            
        gridSearch[f"{n_estimators}_{min_samples_split}"] = scores
        percentBuys[f"{n_estimators}_{min_samples_split}"] = percent_buys

gridSearch.to_parquet("gridSearch.parquet")
percentBuys.to_parquet("percentBuys.parquet")

print(gridSearch.iloc[-5:])
print(percentBuys.iloc[-5:])