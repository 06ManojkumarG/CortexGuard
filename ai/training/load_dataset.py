import pandas as pd


DATASET_PATH = "datasets/combined_dataset.csv"


df = pd.read_csv(DATASET_PATH)


print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", list(df.columns))
print()
print("Label counts:")
print(df["label"].value_counts())
print()
print("Mode counts:")
print(df["mode"].value_counts())