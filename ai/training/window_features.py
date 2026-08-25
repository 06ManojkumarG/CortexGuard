import pandas as pd


WINDOW_SIZE = 5

BASE_FEATURES = [
    "cpu",
    "ram",
    "heap",
    "stack",
    "temperature",
    "current",
    "speed",
]


def build_window_features(window_df):
    if len(window_df) != WINDOW_SIZE:
        raise ValueError(
            f"Expected {WINDOW_SIZE} rows, got {len(window_df)}"
        )

    features = {}

    for feature in BASE_FEATURES:
        values = window_df[feature]

        features[f"{feature}_mean"] = values.mean()
        features[f"{feature}_min"] = values.min()
        features[f"{feature}_max"] = values.max()

        features[f"{feature}_trend"] = (
            values.iloc[-1] - values.iloc[0]
        )

    return features