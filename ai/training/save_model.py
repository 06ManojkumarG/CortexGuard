import os

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score


DATASET_PATH = "datasets/combined_dataset.csv"

MODEL_PATH = "ai/models/cortexguard_decision_tree.joblib"

FEATURE_COLUMNS = [
    "cpu",
    "ram",
    "heap",
    "stack",
    "temperature",
    "current",
    "speed",
]

TARGET_COLUMN = "label"


df = pd.read_csv(DATASET_PATH)

X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMN]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


model = DecisionTreeClassifier(
    class_weight="balanced",
    random_state=42,
)


model.fit(
    X_train,
    y_train,
)


predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions,
)


print(
    f"Validation accuracy: "
    f"{accuracy * 100:.2f}%"
)


# Retrain the selected model using all available data
model.fit(X, y)


os.makedirs(
    os.path.dirname(MODEL_PATH),
    exist_ok=True,
)


model_package = {
    "model": model,
    "features": FEATURE_COLUMNS,
    "model_type": "DecisionTreeClassifier",
}


joblib.dump(
    model_package,
    MODEL_PATH,
)


print("Final model trained on all 877 samples.")
print(f"Model saved to: {MODEL_PATH}")