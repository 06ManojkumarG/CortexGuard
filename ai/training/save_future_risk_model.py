import os

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


TRAIN_FILE = "datasets/future_risk_train_3class.csv"
TEST_FILE = "datasets/future_risk_test_3class.csv"

MODEL_PATH = "ai/models/cortexguard_future_risk_random_forest.joblib"


EXCLUDED_COLUMNS = [
    "sequence",
    "fault_mode",
    "window_start_step",
    "window_end_step",
    "target_step",
    "future_risk",
]


train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)


FEATURE_COLUMNS = [
    column
    for column in train_df.columns
    if column not in EXCLUDED_COLUMNS
]


X_train = train_df[FEATURE_COLUMNS]
y_train = train_df["future_risk"]

X_test = test_df[FEATURE_COLUMNS]
y_test = test_df["future_risk"]


model = RandomForestClassifier(
    n_estimators=200,
    class_weight="balanced",
    random_state=42,
)


model.fit(
    X_train,
    y_train,
)


predictions = model.predict(
    X_test
)

accuracy = accuracy_score(
    y_test,
    predictions,
)


print(
    f"Validation accuracy: "
    f"{accuracy * 100:.2f}%"
)


# Retrain using all available 3-class future-risk windows
full_df = pd.concat(
    [
        train_df,
        test_df,
    ],
    ignore_index=True,
)

X_full = full_df[FEATURE_COLUMNS]
y_full = full_df["future_risk"]


model.fit(
    X_full,
    y_full,
)


os.makedirs(
    os.path.dirname(MODEL_PATH),
    exist_ok=True,
)


model_package = {
    "model": model,
    "features": FEATURE_COLUMNS,
    "model_type": "RandomForestClassifier",
    "window_size": 5,
    "lookahead": 5,
    "classes": [
        "NORMAL",
        "WARNING",
        "HIGH_RISK",
    ],
}


joblib.dump(
    model_package,
    MODEL_PATH,
)


print(
    "Final future-risk model trained "
    "on all 2000 windows."
)

print(
    "Feature count:",
    len(FEATURE_COLUMNS),
)

print(
    "Model saved to:",
    MODEL_PATH,
)