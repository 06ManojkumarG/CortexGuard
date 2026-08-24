import csv
import os

from data_processing.telemetry_schema import TELEMETRY_FIELDS


class TelemetryLogger:
    def __init__(self, file_path):
        self.file_path = file_path

    def initialize_file(self):
        folder = os.path.dirname(self.file_path)

        if folder:
            os.makedirs(folder, exist_ok=True)

        file_exists = os.path.exists(self.file_path)

        if not file_exists:
            with open(
                self.file_path,
                mode="w",
                newline="",
                encoding="utf-8",
            ) as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=TELEMETRY_FIELDS,
                )

                writer.writeheader()

    def log_sample(self, sample):
        with open(
            self.file_path,
            mode="a",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=TELEMETRY_FIELDS,
            )

            writer.writerow(sample)