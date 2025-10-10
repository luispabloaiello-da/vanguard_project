# Low-Level Design (LLD) — Vanguard CX Funnel Experiment

1) Configuration
- ALPHA = 0.05
- THRESHOLD_DIFF = 0.05
- IQR_K = 3.0
- CANONICAL_STEPS = [start, step_1, step_2, step_3, confirm]

2) Data Loading & Standardization (_main_.ipynb)
- Read raw TXT; dtypes enforced; timestamps UTC.
- Sort by (client_id, visitor_id, visit_id, date_time).
- Keep only canonical steps; persist clean CSVs.

3) Sessionization & Back-Jumps (vanguard_funnel_kpis_.ipynb)
- Map steps→indices; delta = diff; back-jump if delta<0.
- Aggregate n_back_jumps per session.
- Collapse to last-occurrence per step and confirm.
- Derive reach flags, completed, hop durations, t_total, and outcome label.
- Save proc_*_clean.csv and *_anomalies.csv with reason codes.

4) KPI Computation (functions.py)
- kpis_from_processes: denominator N = reached_start; compute conversion/drop-off per hop; completion_rate; error_rate; time means; avg_back_jumps.
- step_dropoff_table: compact transitions for funnel.

5) Outlier Handling (vanguard_funnel_outliers_viz.ipynb)
- IQR filter for time metrics with k=IQR_K; save *_no_out.csv; log removals.

6) Statistical Tests (hypotesis_testing.ipynb)
- two_proportion_ztest for completion (larger), threshold (diff0=0.05), error (smaller).
- welch_t_one_sided for times (alternative=less).

7) Balance Checks (demographic_analysis_viz.ipynb)
- t-test/KS + SMD for numeric; χ² for categorical; export balance table CSV.

8) Figures & Reporting
- Funnel bars w/ 95% Wilson CIs; drop-off ladder; time distributions; correlation heatmap.
- Save all plots under figures/ with consistent filenames.

9) Error Handling & Logging
- Anomalies flagged and excluded from KPI denominators; reasons persisted.
- Guard division by zero; surface NaNs with warnings.

10) Complexity & Performance
- Vectorized Pandas ops; groupby per session; scalable to millions of rows.

11) Testing Notes
- Assertions: monotonicity after collapse; outcomes sum to N; denominator checks.
- Manual trace: random session before/after collapse.

12) Security & Privacy
- Pseudonymous IDs only; no PII in outputs.
