import pandas as pd

from window_features import (
    WINDOW_SIZE,
    build_window_features,
)


INPUT_FILE = "datasets/transition_telemetry.csv"
OUTPUT_FILE = "datasets/future_risk_windows.csv"
LOOKAHEAD = 5


df = pd.read_csv(INPUT_FILE)

window_rows = []


for sequence_id, sequence_df in df.groupby(
    "sequence",
    sort=False,
):
    sequence_df = sequence_df.reset_index(drop=True)

    for start_index in range(
        0,
        len(sequence_df) - WINDOW_SIZE - LOOKAHEAD + 1,
    ):
        end_index = start_index + WINDOW_SIZE

        window_df = sequence_df.iloc[
            start_index:end_index
        ]

        features = build_window_features(
            window_df
        )

        features["sequence"] = sequence_id
        features["fault_mode"] = (
            window_df.iloc[-1]["fault_mode"]
        )

        features["window_start_step"] = (
            int(window_df.iloc[0]["step"])
        )

        features["window_end_step"] = (
            int(window_df.iloc[-1]["step"])
        )

        target_index = (
            end_index - 1 + LOOKAHEAD
        )

        features["target_step"] = int(
            sequence_df.iloc[target_index]["step"]
        )

        features["future_risk"] = (
            sequence_df.iloc[target_index]["future_risk"]
        )

        window_rows.append(features)


window_dataset = pd.DataFrame(
    window_rows
)

window_dataset.to_csv(
    OUTPUT_FILE,
    index=False,
)


print(
    "Future-risk window dataset created successfully."
)

print(
    "Window size:",
    WINDOW_SIZE,
)

print(
    "Total windows:",
    len(window_dataset),
)

print()
print(
    "Risk distribution:"
)

print(
    window_dataset["future_risk"].value_counts()
)

print()
print(
    "Windows by sequence:"
)

print(
    window_dataset["sequence"].value_counts()
)

print()
print(
    "Output:",
    OUTPUT_FILE,
)