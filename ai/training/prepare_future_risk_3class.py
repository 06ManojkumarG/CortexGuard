import pandas as pd


TRAIN_INPUT = "datasets/future_risk_train.csv"
TEST_INPUT = "datasets/future_risk_test.csv"

TRAIN_OUTPUT = "datasets/future_risk_train_3class.csv"
TEST_OUTPUT = "datasets/future_risk_test_3class.csv"


train_df = pd.read_csv(TRAIN_INPUT)
test_df = pd.read_csv(TEST_INPUT)


train_3class = train_df[
    train_df["future_risk"] != "FAULT"
].copy()

test_3class = test_df[
    test_df["future_risk"] != "FAULT"
].copy()


train_3class.to_csv(
    TRAIN_OUTPUT,
    index=False,
)

test_3class.to_csv(
    TEST_OUTPUT,
    index=False,
)


print("3-class future-risk datasets created.")

print()
print("Training windows:", len(train_3class))
print("Testing windows:", len(test_3class))

print()
print("Training distribution:")
print(
    train_3class["future_risk"].value_counts()
)

print()
print("Testing distribution:")
print(
    test_3class["future_risk"].value_counts()
)

print()
print("Training output:", TRAIN_OUTPUT)
print("Testing output:", TEST_OUTPUT)