import pandas as pd


DATASET_PATH = "datasets/combined_dataset.csv"

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


print("Feature preparation complete.")
print("X shape:", X.shape)
print("y shape:", y.shape)

print()
print("Features:")
print(list(X.columns))

print()
print("Target counts:")
print(y.value_counts())