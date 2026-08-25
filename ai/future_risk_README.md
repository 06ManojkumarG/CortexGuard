# CortexGuard Milestone 4 — Future Fault Prediction

## Purpose

Milestone 4 adds early-warning prediction to CortexGuard.

Milestone 3 detects the current condition:

- NORMAL
- FAULT

Milestone 4 predicts the near-future risk:

- NORMAL
- WARNING
- HIGH_RISK

## Prediction Architecture

The future-risk model uses a sliding telemetry window.

Window size:

5 samples

Prediction look-ahead:

5 samples

The model therefore uses the recent telemetry trend to predict the
risk level several samples ahead.

## Base Telemetry Features

- cpu
- ram
- heap
- stack
- temperature
- current
- speed

## Window Features

For each base feature, the following values are calculated:

- mean
- minimum
- maximum
- trend

This produces:

28 model input features.

## Transition Dataset

A simulated transition dataset was generated to represent gradual
movement from normal operation toward different fault conditions.

Fault transition types:

- CPU_FAULT
- MEMORY_FAULT
- STACK_FAULT
- TIMING_FAULT
- APPLICATION_FAULT

Sequences per fault type:

20

Total sequences:

100

Samples per sequence:

30

Total transition telemetry rows:

3000

## Transition Risk Stages

Each simulated transition progresses through:

NORMAL
→ WARNING
→ HIGH_RISK
→ FAULT

The FAULT endpoint is retained in the transition data to define the
trajectory, but the Milestone 4 AI model does not classify FAULT.

Current FAULT detection remains the responsibility of Milestone 3.

## Future-Risk Window Dataset

Window size:

5

Look-ahead:

5

Total future-risk windows:

2100

The target label is taken from the telemetry state five samples after
the observed window.

## Leakage-Safe Split

Entire transition sequences were split between training and testing.

Training sequences:

80

Testing sequences:

20

Training windows:

1680

Testing windows:

420

Sequence overlap:

0

This prevents neighboring windows from the same transition sequence
appearing in both training and testing.

## Three-Class Future-Risk Dataset

Windows whose future target was already FAULT were excluded from the
Milestone 4 prediction problem.

Final classes:

- NORMAL
- WARNING
- HIGH_RISK

Training windows:

1600

Testing windows:

400

Training distribution:

- NORMAL: 480
- WARNING: 720
- HIGH_RISK: 400

Testing distribution:

- NORMAL: 120
- WARNING: 180
- HIGH_RISK: 100

## Baseline Models

Three models were evaluated.

### Logistic Regression

Accuracy:

88.50%

### Decision Tree

Accuracy:

86.75%

### Random Forest

Accuracy:

91.00%

## Selected Model

Random Forest was selected as the Milestone 4 future-risk predictor.

Test-set results:

- Accuracy: 91.00%
- NORMAL recall: 95%
- WARNING recall: 88%
- HIGH_RISK recall: 91%

Confusion matrix:

Actual NORMAL:
- 114 predicted NORMAL
- 6 predicted WARNING
- 0 predicted HIGH_RISK

Actual WARNING:
- 6 predicted NORMAL
- 159 predicted WARNING
- 15 predicted HIGH_RISK

Actual HIGH_RISK:
- 0 predicted NORMAL
- 9 predicted WARNING
- 91 predicted HIGH_RISK

## Saved Model

Saved model:

ai/models/cortexguard_future_risk_random_forest.joblib

The saved model package contains:

- trained Random Forest model
- 28 feature names
- model type
- window size
- look-ahead value
- supported prediction classes

The final model was retrained using all 2000 available three-class
future-risk windows.

## Saved-Model Functional Test

Three manually constructed 5-sample telemetry windows were tested.

Results:

Stable Normal Window:

- Prediction: NORMAL
- NORMAL probability: 100.00%

Warning Window:

- Prediction: WARNING
- WARNING probability: 51.50%

High Risk Window:

- Prediction: HIGH_RISK
- HIGH_RISK probability: 75.00%

## CortexGuard AI Architecture

Current-state model:

Decision Tree

Output:

NORMAL / FAULT

Future-risk model:

Random Forest

Output:

NORMAL / WARNING / HIGH_RISK

These models remain separate so that current fault detection and
future-risk prediction do not overlap.

## Important Limitations

The current Milestone 4 model was trained using simulated transition
telemetry.

The 91.00% result applies only to the current Phase 1 simulated test
dataset.

The transition patterns, risk stages, window size, look-ahead horizon,
and thresholds have not yet been validated using real STM32 hardware.

Future hardware datasets should be used to retrain and evaluate the
model before making real-world reliability claims.

## Milestone Boundary

Milestone 4 builds and validates the future-risk predictor only.

Dashboard integration belongs to Milestone 5.