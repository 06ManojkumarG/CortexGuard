import pandas as pd
from sklearn.model_selection import train_test_split


INPUT_FILE = "datasets/future_risk_windows.csv"

TRAIN_FILE = "datasets/future_risk_train.csv"
TEST_FILE = "datasets/future_risk_test.csv"


df = pd.read_csv(INPUT_FILE)


sequence_table = (
    df[
        [
            "sequence",
            "fault_mode",
        ]
    ]
    .drop_duplicates()
    .reset_index(drop=True)
)


train_sequences, test_sequences = train_test_split(
    sequence_table,
    test_size=0.20,
    random_state=42,
    stratify=sequence_table["fault_mode"],
)


train_ids = set(
    train_sequences["sequence"]
)

test_ids = set(
    test_sequences["sequence"]
)


train_df = df[
    df["sequence"].isin(train_ids)
].copy()

test_df = df[
    df["sequence"].isin(test_ids)
].copy()


train_df.to_csv(
    TRAIN_FILE,
    index=False,
)

test_df.to_csv(
    TEST_FILE,
    index=False,
)


print("Sequence-level split complete.")

print()
print("Training sequences:", len(train_ids))
print("Testing sequences:", len(test_ids))

print()
print("Training windows:", len(train_df))
print("Testing windows:", len(test_df))

print()
print("Training fault modes:")
print(
    train_sequences["fault_mode"].value_counts()
)

print()
print("Testing fault modes:")
print(
    test_sequences["fault_mode"].value_counts()
)

print()
print("Training risk distribution:")
print(
    train_df["future_risk"].value_counts()
)

print()
print("Testing risk distribution:")
print(
    test_df["future_risk"].value_counts()
)

print()
print(
    "Sequence overlap:",
    len(train_ids.intersection(test_ids)),
)

print()
print("Outputs:")
print(TRAIN_FILE)
print(TEST_FILE)