# Vanguard Funnel KPIs — Functions & Workflow (README)

This document explains what each helper and pipeline function does and why it’s needed.

## Overview
- Standardizes step labels and timestamps.
- Groups events by process (`client_id`, `visitor_id`, `visit_id`).
- Detects **back‑steps** and keeps only the **last confirm** per process.
- Builds one **summary row per process** and aggregates **KPIs** (completion, drop‑off, time, error rates).

## Data Inputs
- `df_web_data` with `client_id`, `visitor_id`, `visit_id`, `process_step`, `date_time`
- `df_demo_control` (or demo for Test) with `client_id`

## Functions
1) `_standardize_steps(df)` → normalize steps; drop non‑canonical.
2) `_to_utc(series)` → parse timestamps; enforce UTC.
3) `prepare_web_for_group(df_web_data, df_demo_group)` → filter to cohort, standardize, UTC, sort.
4) `compute_back_jumps(w_full)` → map steps→indices; flag `is_back_jump`; aggregate `n_back_jumps`.
5) `collapse_last_per_step_and_last_confirm(wf)` → last confirm and last per step.
6) `summarize_processes(wf2, back)` → one row per process; flags, durations, `t_total`, outcome.
7) `kpis_from_processes(proc)` → completion, step rates, outcome mix, time medians, avg back‑jumps.
8) `step_dropoff_table(proc)` → `n_from`, `n_to`, conversion%, dropoff% per hop.

## End‑to‑End Example
```python
w_control = prepare_web_for_group(df_web_data, df_demo_control)
wf, back = compute_back_jumps(w_control)
wf2 = collapse_last_per_step_and_last_confirm(wf)
proc_control = summarize_processes(wf2, back)
kpis_control = kpis_from_processes(proc_control)
dropoff_control = step_dropoff_table(proc_control)
```

## KPI Quick Reference
- Completion rate: `% confirm / starters`
- Step rates: `% of starters reaching each step`
- Successful vs completed_with_errors vs unsuccessful
- Time KPIs: **median minutes** per hop and total
- Error level: **average back‑jumps** per process

## Sanity Checks
- Fix labels with `_standardize_steps`; run `_to_utc` before timing; `collapse_last_per_step_and_last_confirm` handles repeats; use medians/IQR or IQR‑filtering for time outliers.
