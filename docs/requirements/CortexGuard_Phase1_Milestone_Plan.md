Milestone 1 — PC dashboard



Create a basic application on the PC.



It should display live graphs.



For example:



CPU Usage

&#x20;  │

100│

&#x20;75│             ╱

&#x20;50│      ╱─────╯

&#x20;25│─────╯

&#x20;  └──────────────── time



And similar graphs for:



CPU

RAM/heap

stack

temperature

current

speed



Also display:



SYSTEM STATUS



NORMAL



Later:



SYSTEM STATUS



⚠ ANOMALY DETECTED



And eventually:



FAULT PROBABILITY



78%

Milestone 2 — Data collection



This is where the AI work really begins.



Run your embedded application many times.



Collect:



Dataset A — Normal



Normal operating conditions.



Dataset B — CPU abnormality



Artificially increase CPU workload.



Dataset C — Memory abnormality



Increase memory/heap pressure.



Dataset D — Timing abnormality



Create task delays.



Dataset E — Application anomaly



Introduce abnormal sensor/control values.



Save everything as CSV.



Example:



CPU,Heap,Stack,Temp,Current,Speed,Label

32,45,38,42,1.2,1500,NORMAL

35,46,39,42,1.3,1502,NORMAL

78,70,65,44,1.5,1490,FAULT

85,82,72,45,1.6,1480,FAULT

Milestone 3 — First AI model



Do not start with deep learning.



Your team is learning everything from scratch. A simple ML model is much more appropriate for the first demonstration.



Start with something like:



Decision Tree

Random Forest

Logistic Regression



The model receives the telemetry features:



CPU

Heap

Stack

Temperature

Current

Speed

...



And predicts:



NORMAL



or



FAULT

Milestone 4 — "Future fault" prediction



This is the more interesting part of your faculty's requirement.



There are actually two different AI problems:



Problem A — Current fault detection



"Is the system abnormal right now?"



Output:



NORMAL

FAULT

Problem B — Early warning / future fault prediction



"Does the current behavior indicate that a fault may occur soon?"



Output could be:



NORMAL

WARNING

HIGH RISK



For example:



10:00 → NORMAL

10:01 → NORMAL

10:02 → WARNING

10:03 → HIGH RISK

10:04 → FAULT



This gives you a much stronger faculty demonstration.



We can initially implement this using time-windowed telemetry features rather than jumping into complicated AI architectures.



Milestone 5 — Integrate AI with the dashboard



Now combine everything:



&#x20;            STM32

&#x20;              │

&#x20;              │ runtime telemetry

&#x20;              ↓

&#x20;            USB

&#x20;              │

&#x20;              ↓

&#x20;       PC CortexGuard

&#x20;              │

&#x20;      ┌───────┴────────┐

&#x20;      ↓                ↓

&#x20;   Graphs           AI Model

&#x20;                        │

&#x20;            ┌───────────┼──────────┐

&#x20;            ↓           ↓          ↓

&#x20;          NORMAL     WARNING      FAULT

&#x20;                        │

&#x20;                        ↓

&#x20;                 Future Risk %



This is the Phase 1 centerpiece.



Milestone 6 — Phase 1 demonstration



Your faculty should be able to watch you do something like this:



Step 1



Start STM32 application.



Dashboard shows:



SYSTEM: NORMAL



Step 2



Show live graphs.



CPU, memory, sensor values, etc.



Step 3



Introduce an abnormal condition.



For example, increase CPU workload.



Step 4



Graphs start changing.



Step 5



AI detects the abnormal pattern.



ANOMALY DETECTED

Probability: 87%

Step 6



Demonstrate early warning.



Before the actual simulated fault:



⚠ POTENTIAL FAULT

Risk: 72%

Step 7



Fault occurs.



FAULT DETECTED



That is a very strong Phase 1 demo without requiring you to build the final hardware system yet.

