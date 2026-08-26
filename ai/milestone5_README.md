\# CortexGuard — Milestone 5



\## AI Dashboard Integration



Milestone 5 integrates the previously trained CortexGuard AI models into the live monitoring dashboard.



The milestone combines current fault detection with future fault-risk prediction and presents both results in real time.



\---



\## 1. Milestone Objective



The objective of Milestone 5 is to connect the CortexGuard AI pipeline to live telemetry and expose the AI results through the dashboard.



The integrated system provides:



\- Current system-state prediction

\- Future fault-risk prediction

\- AI prediction confidence

\- Unified system status

\- Visual warning and fault states

\- Live operation across all simulator modes



\---



\## 2. AI Models Integrated



\### Current-State Fault Detection



Model:



`ai/models/cortexguard\_decision\_tree.joblib`



Purpose:



Detect the current system condition.



Output classes:



\- NORMAL

\- FAULT



Input feature count:



7



\---



\### Future-Risk Prediction



Model:



`ai/models/cortexguard\_future\_risk\_random\_forest.joblib`



Purpose:



Predict developing fault risk from recent telemetry trends.



Output classes:



\- NORMAL

\- WARNING

\- HIGH\_RISK



Input feature count:



28



\---



\## 3. AI Inference Layer



Milestone 5 introduced:



`ai/inference/ai\_engine.py`



The AIEngine loads both saved models and exposes separate prediction paths for:



\- Current-state prediction

\- Future-risk prediction



This keeps model loading and inference separate from the dashboard UI logic.



\---



\## 4. Rolling Telemetry Window



Future-risk prediction uses a rolling telemetry window.



Window size:



`5 samples`



Each live telemetry sample contains:



\- CPU

\- RAM

\- Heap

\- Stack

\- Temperature

\- Current

\- Speed



The dashboard maintains only the latest five samples.



Once five samples are available, CortexGuard generates the 28 window features required by the future-risk model.



\---



\## 5. Window Features



For each of the seven telemetry signals, CortexGuard calculates:



\- Mean

\- Minimum

\- Maximum

\- Trend



This produces:



`7 signals × 4 features = 28 features`



These features are passed to the Milestone 4 future-risk Random Forest model.



\---



\## 6. Unified AI Status Logic



CortexGuard combines current-state detection and future-risk prediction using the following priority:



1\. Current AI = FAULT → FAULT

2\. Future AI = HIGH\_RISK → HIGH\_RISK

3\. Future AI = WARNING → WARNING

4\. Otherwise → NORMAL



Current detected faults therefore have the highest priority.



This prevents future-risk information from overriding an already detected active fault.



\---



\## 7. Dashboard AI Integration



The CortexGuard dashboard now displays:



\- SYSTEM STATUS

\- CURRENT AI STATE

\- FUTURE RISK

\- RISK CONFIDENCE



Example states include:



`CURRENT AI STATE: NORMAL`



`CURRENT AI STATE: FAULT`



`FUTURE RISK: NORMAL`



`FUTURE RISK: WARNING`



`FUTURE RISK: HIGH\_RISK`



The risk-confidence field displays the predicted future-risk class probability.



\---



\## 8. Visual Status Behavior



Dashboard visual states were added for:



\### NORMAL



Normal dashboard presentation.



\### WARNING



A warning visual state indicates developing telemetry risk.



\### HIGH\_RISK



A stronger warning visual state indicates elevated predicted fault risk.



\### FAULT



The strongest visual state indicates that the current-state AI has detected an active fault.



\---



\## 9. Integration Test Results



Milestone 5 was tested across all six CortexGuard simulator modes.



The following integration tests passed:



\- NORMAL

\- CPU\_FAULT

\- MEMORY\_FAULT

\- STACK\_FAULT

\- TIMING\_FAULT

\- APPLICATION\_FAULT



During testing, the following components continued operating together:



\- Live telemetry

\- Telemetry graphs

\- Current-state AI

\- Future-risk AI

\- Risk confidence

\- Unified status logic

\- Dashboard status styling



\---



\## 10. Regression Testing



The following existing CortexGuard functionality was retested after AI integration:



\- Pause monitoring

\- Resume monitoring

\- Reset graphs

\- CSV telemetry recording

\- Simulator mode switching

\- Repeated dashboard startup

\- Repeated dashboard shutdown



All regression tests passed.



\---



\## 11. Runtime Architecture



CortexGuard Milestone 5 uses the following runtime pipeline:



Live Telemetry



↓



Current-State AI



NORMAL / FAULT



\+



5-Sample Rolling Window



↓



28 Window Features



↓



Future-Risk AI



NORMAL / WARNING / HIGH\_RISK



↓



Unified AI Status



↓



CortexGuard Dashboard



\---



\## 12. Milestone 5 Result



Milestone 5 successfully connects the CortexGuard AI models to the live monitoring dashboard.



The system can now:



\- Detect current faults

\- Analyze recent telemetry trends

\- Predict developing risk

\- Display prediction confidence

\- Combine current and future AI states

\- Present AI status visually in real time



This establishes the live AI monitoring layer required for later CortexGuard development.



\---



\## Milestone Status



\*\*Milestone 5 — AI Dashboard Integration: COMPLETE\*\*



Final validation, backup, repository update, and milestone freeze are performed as part of the Milestone 5 completion procedure.

