import pandas as pd
from sklearn.model_selection import train_test_split


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


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


print("Train/test split complete.")

print()
print("Total samples:", len(df))
print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))

print()
print("Training label counts:")
print(y_train.value_counts())

print()
print("Testing label counts:")
print(y_test.value_counts())