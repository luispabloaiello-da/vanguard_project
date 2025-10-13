# Vanguard CX Funnel A/B Test — Project README

## Overview
This repository evaluates whether a redesigned web UI (Test) improves client completion of a 5‑step funnel relative to the legacy UI (Control). It includes data preparation, KPI computation, outlier handling, and hypothesis testing with a +5 percentage‑point cost‑effectiveness threshold.

## Live Assets

- **Slides (Canva):** https://www.canva.com/design/DAG1X8OYFCo/CqLrqcE1ZaBMi2s_BbKmIw/edit?utm_content=DAG1X8OYFCo&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton
- **Interactive Tableau Dashboard:** https://public.tableau.com/app/profile/luis.pablo.aiello/viz/VanguardCXFunnel-ABResults/Dashboard1?publish=yes

## Repository Structure
.
├── _main_.ipynb                        # Orchestration & initial EDA
├── demographic_analysis_viz.ipynb      # Group balance & demographics
├── vanguard_funnel_kpis_.ipynb         # KPI pipeline per cohort (control/test)
├── vanguard_funnel_outliers_viz.ipynb  # Outlier viz & filtered datasets
├── hypotesis_testing.ipynb             # Statistical tests & decisions
├── analysis_web_data_control.ipynb     # (optional) cohort-specific analysis
├── analysis_web_data_test.ipynb        # (optional) cohort-specific analysis
├── functions.py                        # Helper utilities (z-tests, Welch, KPIs, etc.)
├── config.yaml                         # Paths for inputs/outputs/figures
└── figures/                            # Saved charts

## Data Inputs
- df_final_demo.txt: demographics (age, tenure, gender, accounts, balances, logins, calls)
- df_final_experiment_clients.txt: treatment/control assignment
- df_final_web_data_pt_1.txt, df_final_web_data_pt_2.txt: event logs (process_step, date_time, ids)

> Paths are configured in config.yaml under paths:. Update if needed.

## KPIs
- Completion rate: % of sessions reaching confirm out of those that reached start.
- Step conversion/drop-off: rates between adjacent steps.
- Error rate: back-jumps (later → earlier step) detected per session.
- Time KPIs: minutes per hop and total (t_total).
- Outcome mix: % successful / completed_with_errors / fail.

## Statistical Tests
- Completion (Test vs Control): one-sided 2‑proportion z-test (H1: Test > Control).
- Cost-effectiveness threshold: 2‑proportion z with diff0=0.05 (H1: Test − Control > 5 pp).
- Error rate: one-sided 2‑proportion z (H1: Test < Control).
- Time to complete: Welch’s t (one-sided; H1: Test faster). If non-normal, also report Mann–Whitney.

## How to Run
1) _main_.ipynb
2) vanguard_funnel_kpis_.ipynb
3) vanguard_funnel_outliers_viz.ipynb
4) demographic_analysis_viz.ipynb
5) hypotesis_testing.ipynb

## Outputs
- Cleaned/aggregated CSVs: proc_control_clean.csv, proc_test_clean.csv, anomalies and no‑outlier variants.
- Funnel & KPI figures in figures/.
- Final hypothesis test cells with z/t statistics, p-values, effect sizes, and decisions.

## Assumptions & Limitations
- Random assignment to Test/Control; balance validated in demographic_analysis_viz.ipynb.
- Time features may be skewed; medians and IQR reported in addition to means.
- Only pseudonymous IDs are processed; no raw PII persisted.

## Reproducibility
- Helpers in functions.py; parameters in config.yaml/notebook constants.
- Anomalies are quarantined in dedicated CSVs with reasons for exclusion.

## Next Steps
- Add device/channel stratification and post-hoc FDR control across secondary tests.
- Package pipeline as a CLI/notebook-agnostic script; schedule on Airflow or Prefect.