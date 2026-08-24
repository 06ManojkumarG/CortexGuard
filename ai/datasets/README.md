# CortexGuard Phase 1 Telemetry Dataset

## Purpose

This dataset contains simulated runtime telemetry collected from the
CortexGuard PC dashboard for Phase 1 machine-learning development.

## Telemetry Fields

- timestamp
- cpu
- ram
- heap
- stack
- temperature
- current
- speed
- mode
- label

## Operating Modes

### NORMAL
Normal simulated system operation.

File:
normal.csv

Label:
NORMAL

### CPU_FAULT
Simulated abnormal CPU workload.

File:
cpu_fault.csv

Label:
FAULT

### MEMORY_FAULT
Simulated abnormal memory usage.

File:
memory_fault.csv

Label:
FAULT

### STACK_FAULT
Simulated abnormal stack usage.

File:
stack_fault.csv

Label:
FAULT

### TIMING_FAULT
Simulated timing/performance abnormality.

File:
timing_fault.csv

Label:
FAULT

### APPLICATION_FAULT
Simulated application/sensor/control abnormality involving
temperature, current, and speed.

File:
application_fault.csv

Label:
FAULT

## Combined Dataset

combined_dataset.csv contains all six operating-mode datasets.

Total samples at Milestone 2 freeze:

877

## Dataset Distribution

- NORMAL: 146
- CPU_FAULT: 147
- MEMORY_FAULT: 147
- STACK_FAULT: 151
- TIMING_FAULT: 143
- APPLICATION_FAULT: 143

## Data Validation

At the Milestone 2 freeze:

- All six datasets use the same telemetry schema.
- No missing values were detected.
- All operating modes were verified.
- All labels were verified.

## Machine Learning Note

The binary dataset is class-imbalanced because five abnormal operating
modes map to the FAULT label while one operating mode maps to NORMAL.

Milestone 3 must account for this during model training and evaluation.

The `mode` column identifies the experiment that produced each sample.
The `label` column represents the binary ground-truth classification.

## Excluded Test Data

The following development/test files are not part of the training dataset:

- test_telemetry.csv
- live_telemetry.csv

## Important

These Phase 1 datasets are currently generated from the CortexGuard
telemetry simulator.

Future STM32 telemetry datasets should preserve the same telemetry
interface wherever possible so the dashboard and AI pipeline can be
integrated without unnecessary architectural changes.