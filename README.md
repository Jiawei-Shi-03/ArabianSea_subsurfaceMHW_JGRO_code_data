**This is an initial peer-review version of the repository.**
# ArabianSea_subsurfaceMHW_JGRO_code_data

This repository provides selected processed diagnostic tables and example analysis scripts associated with the manuscript:

**“Preconditioning of Arabian Sea subsurface marine heatwaves through a sea-level–thermocline–100 m temperature pathway”**

The manuscript examines Arabian Sea subsurface warm events during 1993-2024 and identifies a sea-level-thermocline-100 m temperature pathway that preconditions subsurface marine heatwave development.

This repository is intended to support transparency and peer-review reproducibility for the key mechanistic-closure and satellite sea-level precursor diagnostics used in the manuscript and Supporting Information.

## Repository Status

This is an initial peer-review version of the repository.

The current release includes selected processed diagnostic tables and example MATLAB/Python scripts related to the near-miss control analysis, thermocline-displacement estimate, and satellite sea-level precursor-skill diagnostics.

Additional processed tables, plotting scripts, or full workflow scripts may be added in later releases.

## Current Contents

| File | Description |
|---|---|
| `StepNM_near_miss_pre_onset_event_values.csv` | Processed event-level values for the near-miss control analysis. This file supports the comparison between true 100 m warm-event onsets and control groups, including failed P90 spells, P85-P90 near-miss warm days, and random same-season non-event days. |
| `StepTD_daily_T100_displacement_estimate.csv` | Daily processed diagnostics for the thermocline-displacement estimate of 100 m temperature anomalies. This file includes observed and displacement-estimated 100 m temperature anomaly information used to evaluate the D26–T100 relationship. |
| `StepSK_DUACS_SLA_onset_composites.csv` | Processed onset-composite diagnostics for DUACS satellite sea-level anomaly precursor analysis. |
| `StepSK_DUACS_SLA_AUC_skill_summary.csv` | Summary statistics for the DUACS sea-level anomaly precursor-skill analysis, including ROC/AUC-based diagnostics. |
| `Merge_StepNM_StepTD_StepSK.m` | MATLAB example script for combining selected near-miss, thermocline-displacement, and satellite precursor diagnostics into a mechanistic-closure figure workflow. |
| `mechanistic_closure_satellite_precursor_skill.py` | Python example script for reading selected processed diagnostic tables and reproducing/previewing parts of the mechanistic-closure and satellite precursor diagnostics. |
| `LICENSE` | Repository license information. |


## External Data Sources

Raw public datasets are **not redistributed** in this repository. They should be obtained from their original data providers, as described in the manuscript Open Research / Data Availability section.

The main external datasets used in the study include:

- GLORYS ocean reanalysis from the Copernicus Marine Service
- DUACS satellite altimetry sea-level products from the Copernicus Marine Service
- ARMOR3D observation-constrained subsurface temperature products from the Copernicus Marine Service
- ERA5 atmospheric reanalysis from the Copernicus Climate Data Store / ECMWF
- NOAA OISST v2.1 sea surface temperature
- Niño3.4 and Dipole Mode Index time series from NOAA PSL

Users should download these raw datasets from the official data portals if they wish to reproduce the full raw-data workflow.

## Software

The original analysis was developed primarily in MATLAB and python.

- Example MATLAB script: `Merge_StepNM_StepTD_StepSK.m`
- Example Python script: `mechanistic_closure_satellite_precursor_skill.py`
- Processed data format: CSV

The Python example script requires a standard scientific Python environment, including common packages such as `pandas`, `numpy`, and `matplotlib`.

## How to Use the Processed Data

The processed CSV files can be opened directly in MATLAB, Python, R, Excel, or other data-analysis software.

Example in MATLAB:

In matlab:
T = readtable('StepTD_daily_T100_displacement_estimate.csv');

In python:
import pandas as pd
T = pd.read_csv("StepTD_daily_T100_displacement_estimate.csv")
