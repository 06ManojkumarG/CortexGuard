# CortexGuard Milestone 3 — First AI Model

## Purpose

Milestone 3 builds the first machine-learning fault classifier for CortexGuard.

The model receives runtime telemetry features and predicts:

- NORMAL
- FAULT

## Dataset

Source:

datasets/combined_dataset.csv

Total samples:

877

Class distribution:

- NORMAL: 146
- FAULT: 731

## Input Features

The model uses these 7 telemetry features:

- cpu
- ram
- heap
- stack
- temperature
- current
- speed

The following columns are intentionally excluded from model input:

- timestamp
- mode

`mode` is excluded because it would leak the correct class into the model.

## Class Imbalance

The dataset is imbalanced:

- NORMAL: 146
- FAULT: 731

The training process uses:

class_weight="balanced"

This gives more importance to the minority NORMAL class without deleting fault samples or duplicating normal samples.

## Train/Test Split

The dataset was split using:

- Training: 80%
- Testing: 20%
- random_state: 42
- stratify: label

Result:

- Training samples: 701
- Testing samples: 176

## Baseline Models

Three models were evaluated:

### Logistic Regression

Accuracy:

87.50%

### Decision Tree

Accuracy:

98.30%

### Random Forest

Accuracy:

97.73%

## Selected Model

Decision Tree was selected as the Milestone 3 baseline model.

Test-set results:

- Accuracy: 98.30%
- NORMAL recall: approximately 89.66%
- FAULT recall: 100%

Confusion matrix:

Actual NORMAL:
- 26 predicted NORMAL
- 3 predicted FAULT

Actual FAULT:
- 0 predicted NORMAL
- 147 predicted FAULT

The Decision Tree was selected because it detected all FAULT samples in the current held-out simulated test set.

## Saved Model

The final selected model was retrained using all 877 available Phase 1 simulated samples.

Saved model:

ai/models/cortexguard_decision_tree.joblib

The saved package contains:

- trained model
- feature column order
- model type

## Functional Inference Test

The saved model was loaded without retraining and tested using manually constructed telemetry samples.

Results:

- Normal sample → NORMAL
- CPU fault sample → FAULT
- Memory fault sample → FAULT
- Application fault sample → FAULT

## Important Limitations

The current model was trained on simulated telemetry data.

The 98.30% result applies only to the current simulated Phase 1 dataset and must not be presented as validated real-world STM32 performance.

Decision Tree class probabilities may also appear as 0% or 100% because individual tree leaves can contain samples from only one class.

Future hardware datasets should be used to retrain and validate the model.

## Milestone Boundary

Milestone 3 performs current fault classification only:

NORMAL
FAULT

Future-fault / early-warning prediction belongs to Milestone 4.

Dashboard integration belongs to Milestone 5.