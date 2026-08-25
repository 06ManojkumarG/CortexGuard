from future_risk_labels import assign_future_risk


test_cases = [
    {
        "name": "Stable Normal",
        "features": {
            "cpu_trend": 2,
            "ram_trend": 1,
            "heap_trend": 0,
            "stack_trend": 2,
            "temperature_trend": 1,
            "current_trend": 0.1,
            "speed_trend": -20,
        },
    },
    {
        "name": "Warning Trend",
        "features": {
            "cpu_trend": 18,
            "ram_trend": 12,
            "heap_trend": 4,
            "stack_trend": 3,
            "temperature_trend": 3,
            "current_trend": 0.2,
            "speed_trend": -40,
        },
    },
    {
        "name": "High Risk Trend",
        "features": {
            "cpu_trend": 30,
            "ram_trend": 22,
            "heap_trend": 5,
            "stack_trend": 4,
            "temperature_trend": 12,
            "current_trend": 1.2,
            "speed_trend": -220,
        },
    },
]


for test_case in test_cases:
    result = assign_future_risk(
        test_case["features"]
    )

    print(
        test_case["name"],
        "->",
        result,
    )