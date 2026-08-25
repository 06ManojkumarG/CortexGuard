import random

import pandas as pd


OUTPUT_FILE = "datasets/transition_telemetry.csv"

SEQUENCE_LENGTH = 30
SEQUENCES_PER_FAULT = 20

random.seed(42)


FAULT_TARGETS = {
    "CPU_FAULT": {
        "cpu": (85, 98),
        "ram": (35, 65),
        "heap": (30, 55),
        "stack": (25, 55),
        "temperature": (50, 65),
        "current": (1.7, 3.0),
        "speed": (1350, 1500),
    },

    "MEMORY_FAULT": {
        "cpu": (30, 60),
        "ram": (85, 98),
        "heap": (75, 95),
        "stack": (30, 60),
        "temperature": (40, 60),
        "current": (1.3, 2.7),
        "speed": (1350, 1500),
    },

    "STACK_FAULT": {
        "cpu": (30, 60),
        "ram": (35, 65),
        "heap": (30, 60),
        "stack": (85, 98),
        "temperature": (40, 60),
        "current": (1.3, 2.7),
        "speed": (1350, 1500),
    },

    "TIMING_FAULT": {
        "cpu": (50, 75),
        "ram": (40, 70),
        "heap": (30, 60),
        "stack": (30, 65),
        "temperature": (45, 60),
        "current": (1.5, 2.8),
        "speed": (1100, 1350),
    },

    "APPLICATION_FAULT": {
        "cpu": (30, 60),
        "ram": (35, 65),
        "heap": (30, 60),
        "stack": (30, 60),
        "temperature": (70, 90),
        "current": (3.2, 5.0),
        "speed": (700, 1100),
    },
}


NORMAL_BASE = {
    "cpu": 35,
    "ram": 45,
    "heap": 40,
    "stack": 35,
    "temperature": 42,
    "current": 1.4,
    "speed": 1500,
}


rows = []


for fault_mode, targets in FAULT_TARGETS.items():

    for sequence_number in range(SEQUENCES_PER_FAULT):

        sequence_id = (
            f"{fault_mode}_{sequence_number + 1:02d}"
        )

        target_values = {
            feature: random.uniform(
                low,
                high,
            )
            for feature, (low, high)
            in targets.items()
        }

        for step in range(SEQUENCE_LENGTH):

            progress = step / (
                SEQUENCE_LENGTH - 1
            )

            row = {
                "sequence": sequence_id,
                "fault_mode": fault_mode,
                "step": step,
            }

            for feature, start_value in NORMAL_BASE.items():

                target_value = target_values[
                    feature
                ]

                value = (
                    start_value
                    + (
                        target_value
                        - start_value
                    )
                    * progress
                )

                if feature == "current":
                    value += random.uniform(
                        -0.08,
                        0.08,
                    )

                    value = round(
                        value,
                        2,
                    )

                else:
                    value += random.uniform(
                        -2,
                        2,
                    )

                    value = round(
                        value,
                        2,
                    )

                row[feature] = value

            if step < 15:
                risk = "NORMAL"

            elif step < 24:
                risk = "WARNING"

            elif step < 29:
                risk = "HIGH_RISK"

            else:
                risk = "FAULT"

            row["future_risk"] = risk

            rows.append(row)

df = pd.DataFrame(rows)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)


print(
    "Transition telemetry created successfully."
)

print(
    "Rows:",
    len(df),
)

print()
print(
    "Risk distribution:"
)

print(
    df["future_risk"].value_counts()
)

print()
print(
    "Rows by sequence:"
)

print(
    df["sequence"].value_counts()
)

print()
print(
    "Output:",
    OUTPUT_FILE,
)