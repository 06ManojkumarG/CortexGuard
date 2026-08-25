import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


TRAIN_FILE = "datasets/future_risk_train_3class.csv"
TEST_FILE = "datasets/future_risk_test_3class.csv"


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


models = {
    "Logistic Regression": Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=42,
                ),
            ),
        ]
    ),

    "Decision Tree": DecisionTreeClassifier(
        class_weight="balanced",
        random_state=42,
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
    ),
}


print(
    "Future-risk feature count:",
    len(FEATURE_COLUMNS),
)

print(
    "Training windows:",
    len(X_train),
)

print(
    "Testing windows:",
    len(X_test),
)


for name, model in models.items():

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

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
        f"\nAccuracy: "
        f"{accuracy * 100:.2f}%"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            labels=[
                "NORMAL",
                "WARNING",
                "HIGH_RISK",
            ],
            zero_division=0,
        )
    )

    print("Confusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            predictions,
            labels=[
                "NORMAL",
                "WARNING",
                "HIGH_RISK",
            ],
        )
    )