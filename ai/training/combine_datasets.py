import csv
import os


SOURCE_FILES = [
    "normal.csv",
    "cpu_fault.csv",
    "memory_fault.csv",
    "stack_fault.csv",
    "timing_fault.csv",
    "application_fault.csv",
]

OUTPUT_FILE = os.path.join(
    "datasets",
    "combined_dataset.csv",
)


all_rows = []
fieldnames = None


for filename in SOURCE_FILES:
    file_path = os.path.join(
        "datasets",
        filename,
    )

    with open(
        file_path,
        mode="r",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        if fieldnames is None:
            fieldnames = reader.fieldnames

        for row in reader:
            all_rows.append(row)


with open(
    OUTPUT_FILE,
    mode="w",
    newline="",
    encoding="utf-8",
) as output_file:

    writer = csv.DictWriter(
        output_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(all_rows)


print(
    f"Combined dataset created with "
    f"{len(all_rows)} rows."
)