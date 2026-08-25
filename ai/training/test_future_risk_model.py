import joblib
import pandas as pd

from window_features import build_window_features


MODEL_PATH = (
    "ai/models/"
    "cortexguard_future_risk_random_forest.joblib"
)


model_package = joblib.load(
    MODEL_PATH
)

model = model_package["model"]
features = model_package["features"]


test_windows = [
    {
        "name": "Stable Normal Window",
        "rows": [
            {
                "cpu": 34,
                "ram": 44,
                "heap": 39,
                "stack": 35,
                "temperature": 42,
                "current": 1.4,
                "speed": 1500,
            },
            {
                "cpu": 35,
                "ram": 45,
                "heap": 40,
                "stack": 34,
                "temperature": 42,
                "current": 1.4,
                "speed": 1498,
            },
            {
                "cpu": 36,
                "ram": 45,
                "heap": 40,
                "stack": 35,
                "temperature": 43,
                "current": 1.5,
                "speed": 1495,
            },
            {
                "cpu": 35,
                "ram": 46,
                "heap": 41,
                "stack": 35,
                "temperature": 43,
                "current": 1.5,
                "speed": 1492,
            },
            {
                "cpu": 36,
                "ram": 46,
                "heap": 41,
                "stack": 36,
                "temperature": 43,
                "current": 1.5,
                "speed": 1490,
            },
        ],
    },

    {
        "name": "Warning Window",
        "rows": [
            {
                "cpu": 40,
                "ram": 46,
                "heap": 40,
                "stack": 35,
                "temperature": 43,
                "current": 1.5,
                "speed": 1490,
            },
            {
                "cpu": 45,
                "ram": 49,
                "heap": 42,
                "stack": 37,
                "temperature": 45,
                "current": 1.7,
                "speed": 1460,
            },
            {
                "cpu": 50,
                "ram": 52,
                "heap": 44,
                "stack": 39,
                "temperature": 47,
                "current": 1.9,
                "speed": 1430,
            },
            {
                "cpu": 56,
                "ram": 55,
                "heap": 46,
                "stack": 41,
                "temperature": 49,
                "current": 2.1,
                "speed": 1390,
            },
            {
                "cpu": 61,
                "ram": 58,
                "heap": 48,
                "stack": 43,
                "temperature": 51,
                "current": 2.3,
                "speed": 1350,
            },
        ],
    },

    {
        "name": "High Risk Window",
        "rows": [
            {
                "cpu": 58,
                "ram": 60,
                "heap": 50,
                "stack": 45,
                "temperature": 52,
                "current": 2.4,
                "speed": 1340,
            },
            {
                "cpu": 65,
                "ram": 64,
                "heap": 54,
                "stack": 48,
                "temperature": 56,
                "current": 2.8,
                "speed": 1280,
            },
            {
                "cpu": 72,
                "ram": 68,
                "heap": 58,
                "stack": 52,
                "temperature": 60,
                "current": 3.2,
                "speed": 1210,
            },
            {
                "cpu": 79,
                "ram": 72,
                "heap": 62,
                "stack": 56,
                "temperature": 64,
                "current": 3.6,
                "speed": 1130,
            },
            {
                "cpu": 86,
                "ram": 76,
                "heap": 66,
                "stack": 60,
                "temperature": 68,
                "current": 4.0,
                "speed": 1050,
            },
        ],
    },
]


for test_window in test_windows:

    window_df = pd.DataFrame(
        test_window["rows"]
    )

    window_features = (
        build_window_features(
            window_df
        )
    )

    sample_df = pd.DataFrame(
        [window_features],
        columns=features,
    )

    prediction = model.predict(
        sample_df
    )[0]

    probabilities = model.predict_proba(
        sample_df
    )[0]

    probability_map = dict(
        zip(
            model.classes_,
            probabilities,
        )
    )

    print()
    print(test_window["name"])
    print("Prediction:", prediction)

    for class_name in [
        "NORMAL",
        "WARNING",
        "HIGH_RISK",
    ]:
        print(
            f"{class_name} probability:",
            f"{probability_map.get(class_name, 0) * 100:.2f}%",
        )