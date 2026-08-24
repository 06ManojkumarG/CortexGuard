import csv
import os


DATASET_FILES = [
    "normal.csv",
    "cpu_fault.csv",
    "memory_fault.csv",
    "stack_fault.csv",
    "timing_fault.csv",
    "application_fault.csv",
]

EXPECTED_FIELDS = [
    "timestamp",
    "cpu",
    "ram",
    "heap",
    "stack",
    "temperature",
    "current",
    "speed",
    "mode",
    "label",
]


for filename in DATASET_FILES:
    file_path = os.path.join(
        "datasets",
        filename,
    )

    print(f"\nChecking: {filename}")

    with open(
        file_path,
        mode="r",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        if reader.fieldnames == EXPECTED_FIELDS:
            print("Header: OK")
        else:
            print("Header: ERROR")
            print("Found:", reader.fieldnames)

        row_count = 0
        missing_values = 0
        labels = set()
        modes = set()

        for row in reader:
            row_count += 1

            labels.add(row["label"])
            modes.add(row["mode"])

            for field in EXPECTED_FIELDS:
                if row[field] is None or row[field].strip() == "":
                    missing_values += 1

        print("Rows:", row_count)
        print("Missing values:", missing_values)
        print("Modes:", modes)
        print("Labels:", labels)