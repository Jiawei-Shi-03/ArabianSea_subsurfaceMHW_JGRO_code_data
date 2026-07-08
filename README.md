# ArabianSea_subsurfaceMHW_JGRO_code_data
For manuscript-Preconditioning of Arabian Sea subsurface marine heatwaves through a sea-level-thermocline-100 m temperature pathway
## Current Contents

The current repository includes processed diagnostic files related to:

1. **Near-miss control diagnostics**

   These files support the comparison between true 100 m warm-event onsets and control groups, including failed P90 spells, P85–P90 near-miss warm days, and random same-season non-event days.

   Example file:
   - `StepNM_near_miss_pre_onset_event_values.csv`

2. **Thermocline-displacement estimate**

   These files support the estimate of the 100 m temperature anomaly reconstructed from D26 anomalies and the background vertical temperature gradient near 100 m.

   Example file:
   - `StepTD_daily_T100_displacement_estimate.csv`

3. **Satellite sea-level precursor skill**

   These files support the DUACS sea-level anomaly precursor-skill diagnostics, including onset composites and ROC/AUC-based skill summaries.

   Example files:
   - `StepSK_DUACS_SLA_onset_composite.csv`
   - `StepSK_DUACS_SLA_AUC_skill_summary.csv`
For example, in python:
import pandas as pd
T = pd.read_csv("StepTD_daily_T100_displacement_estimate.csv")
