import joblib
import pandas as pd


MODEL_PATH = "ai/models/cortexguard_decision_tree.joblib"


# Load the already-trained model package
model_package = joblib.load(MODEL_PATH)

model = model_package["model"]
features = model_package["features"]


# New telemetry samples that were not explicitly used
# as rows in the training script.
test_samples = [
    {
        "name": "Normal Sample",
        "cpu": 30,
        "ram": 40,
        "heap": 35,
        "stack": 30,
        "temperature": 42,
        "current": 1.3,
        "speed": 1500,
    },
    {
        "name": "CPU Fault Sample",
        "cpu": 90,
        "ram": 55,
        "heap": 45,
        "stack": 40,
        "temperature": 48,
        "current": 1.8,
        "speed": 1400,
    },
    {
        "name": "Memory Fault Sample",
        "cpu": 45,
        "ram": 90,
        "heap": 88,
        "stack": 55,
        "temperature": 46,
        "current": 1.6,
        "speed": 1400,
    },
    {
        "name": "Application Fault Sample",
        "cpu": 40,
        "ram": 50,
        "heap": 45,
        "stack": 40,
        "temperature": 82,
        "current": 4.2,
        "speed": 850,
    },
]


for sample in test_samples:

    sample_name = sample.pop("name")

    sample_df = pd.DataFrame(
        [sample],
        columns=features,
    )

    prediction = model.predict(sample_df)[0]

    probabilities = model.predict_proba(sample_df)[0]

    probability_map = dict(
        zip(
            model.classes_,
            probabilities,
        )
    )

    print()
    print(sample_name)
    print("Prediction:", prediction)

    print(
        "NORMAL probability:",
        f"{probability_map.get('NORMAL', 0) * 100:.2f}%"
    )

    print(
        "FAULT probability:",
        f"{probability_map.get('FAULT', 0) * 100:.2f}%"
    )