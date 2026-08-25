import pandas as pd

from window_features import build_window_features


test_data = pd.DataFrame(
    [
        {
            "cpu": 40,
            "ram": 45,
            "heap": 35,
            "stack": 30,
            "temperature": 42,
            "current": 1.2,
            "speed": 1500,
        },
        {
            "cpu": 48,
            "ram": 47,
            "heap": 36,
            "stack": 32,
            "temperature": 44,
            "current": 1.4,
            "speed": 1470,
        },
        {
            "cpu": 55,
            "ram": 50,
            "heap": 38,
            "stack": 34,
            "temperature": 47,
            "current": 1.7,
            "speed": 1430,
        },
        {
            "cpu": 63,
            "ram": 53,
            "heap": 40,
            "stack": 36,
            "temperature": 50,
            "current": 2.0,
            "speed": 1380,
        },
        {
            "cpu": 72,
            "ram": 56,
            "heap": 42,
            "stack": 38,
            "temperature": 54,
            "current": 2.4,
            "speed": 1320,
        },
    ]
)


features = build_window_features(test_data)


print("Window feature test complete.")

for name, value in features.items():
    print(f"{name}: {value}")