# High-Level Design (HLD) — Vanguard CX Funnel Experiment

## 1) Purpose & Business Outcome
Evaluate whether a redesigned web UI (Test) improves client completion of a 5‑step funnel (Start → Step1 → Step2 → Step3 → Confirm) relative to the legacy UI (Control). The HLD defines the data flow, KPIs, quality gates, and statistical testing to produce defensible, reproducible results and decision recommendations.

**Primary decision**  
Ship new UI if it **increases completion rate** and **meets/exceeds a +5 percentage‑point lift** (cost‑effectiveness threshold), with no unacceptable regressions in time‑to‑complete or error rate.

## 2) Scope
**In‑scope:** data wrangling, KPI computation, anomaly/outlier handling, statistical tests, experiment evaluation, and stakeholder outputs (tables/plots).  
**Out‑of‑scope:** UI implementation, product telemetry changes, and post‑launch monitoring (notebook provides a foundation).

## 3) Inputs & Outputs
### Inputs (from `config.yaml`)
- **Demographics & flags:** `../data/raw/df_final_demo.txt`, `../data/raw/df_final_experiment_clients.txt`
- **Web events (logs):** `../data/raw/df_final_web_data_pt_1.txt`, `../data/raw/df_final_web_data_pt_2.txt`

### Processed / Final Artifacts
- **Cleaned demographics:** `../data/clean/clean_df_demo*.csv`
- **Event log (clean):** `../data/clean/clean_df_web_data.csv`
- **Per‑process, per‑group tables (clean + anomalies):** `../data/clean/proc_control_clean.csv`, `../data/clean/proc_test_clean.csv`, plus `*_anomalies.csv`
- **No‑outlier variants:** `proc_control_no_out.csv`, `proc_test_no_out.csv`
- **Figures:** `../figures/figure1.jpeg` … `figure7.jpeg`

## 4) Logical Architecture
### Stage A — Ingest & Standardize
Load raw files; harmonize step names to canonical set: `['start','step_1','step_2','step_3','confirm']`; coerce timestamps to UTC; sort by `client_id, visitor_id, visit_id, date_time`.

### Stage B — Sessionization & Back‑Jumps
Identify backwards navigation (`delta step_idx < 0`) to derive **error flags** and **n_back_jumps** per session.

### Stage C — Last‑Occurrence Collapsing
Keep only the **last seen** instance of each step and the **last confirm** per session to avoid double‑counting retries.

### Stage D — Process Summary (one row per session)
Compute `reached_*` flags, `completed`, time deltas (minutes) per hop and total, join `n_back_jumps`, and set `outcome ∈ {successful, completed_with_errors, fail}`.

### Stage E — KPIs, Drop‑off, Anomalies
Aggregate KPIs & step drop‑off tables (see `kpis_from_processes`, `step_dropoff_table`). Split anomalies via rules (e.g., Step2 without Step1) for transparency.

### Stage F — Outliers & Robust Sets
Visualize, detect, and remove outliers on time metrics (IQR‑based—parameterized) to create **“no‑outlier”** datasets used in confirmatory tests.

### Stage G — Statistical Testing & Decision
- **Proportions Z‑test** for completion and error rates (one‑sided, supports `diff0=0.05` threshold).  
- **Welch’s t‑test (one‑sided)** for time metrics (does not assume equal variances).  
- Optional stratified checks (age, tenure, etc.) for robustness.

## 5) Data Model (key fields)
- **Identity & session keys:** `client_id`, `visitor_id`, `visit_id`  
- **Event:** `process_step`, `date_time`  
- **Demographics:** `clnt_age`, `clnt_tenure_yr`, `clnt_tenure_mnth`, `gendr`, `num_accts`, `bal`, `calls_6_mnth`, `logons_6_mnth`  
- **Derived (per process):** `reached_start/step_1/step_2/step_3/confirm`, `completed`, `t_start_step1`, `t_step1_step2`, `t_step2_step3`, `t_step3_conf`, `t_total`, `n_back_jumps`, `outcome`

## 6) KPI Definitions
From `kpis_from_processes(proc)` (denominator = `reached_start`):
- **Step rates:** % reaching step_1/2/3  
- **Completion rate:** % with confirm  
- **Outcome mix:** % successful / % completed_with_errors / % fail  
- **Time KPIs:** average minutes per hop and `t_total_avg_min`  
- **Error KPIs:** `n_back_jumps`, `avg_back_jumps`  
- **Step drop‑off tables:** conversion & drop‑off per hop  

> Present **medians & IQRs** alongside means where distributions are skewed (time).

## 7) Quality Controls & Anomaly Policy
- Canonical steps only; anything else → dropped.  
- **Order sanity:** a later step without predecessors → **anomaly**; excluded from “clean” KPIs; saved to `*_anomalies.csv` with reason.  
- Multiple confirms → keep **last**.  
- Back‑jumps → counted as errors; flows can still complete with errors.

## 8) Outlier Policy
Time metrics inspected via visualizations; outliers removed via **IQR** method (k configurable). Produce both **raw** and **no‑outlier** KPIs; hypothesis tests run on **no‑outlier** sets.

## 9) Statistical Testing Design
### 9.1 Completion Rate — effectiveness
- **H0:** (p_test − p_ctrl) ≤ 0  
- **H1:** (p_test − p_ctrl) > 0  
One‑sided **2‑proportion z** with Wilson CIs per group.

### 9.2 Cost‑effectiveness Threshold (+5 pp)
- **H0:** (p_test − p_ctrl) ≤ 0.05  
- **H1:** (p_test − p_ctrl) > 0.05  
Same z‑test with `diff0 = 0.05`. Report z, p, group CIs, and observed lift.

### 9.3 Error Rate — regressions
- **H0:** (err_test − err_ctrl) ≥ 0  
- **H1:** (err_test − err_ctrl) < 0  
One‑sided **2‑proportion z** (“smaller”).

### 9.4 Time to complete — efficiency
- **H0:** μ_test ≥ μ_ctrl  
- **H1:** μ_test < μ_ctrl  
**Welch’s t** one‑sided, with normality check / fallback to Mann–Whitney.

### 9.5 Optional robustness
Stratified completion tests (e.g., by **age band**, **tenure**).  
**Significance:** α = 0.05; for multiple secondary tests, control FDR (Benjamini–Hochberg).

## 10) Module Responsibilities (by notebook)
- `_main_.ipynb` — ingest, merges, EDA entry, write cleaned bases.  
- `vanguard_funnel_kpis_.ipynb` — prepare → back‑jumps → collapse last → summarize → KPIs → drop‑off → save.  
- `vanguard_funnel_outliers_viz.ipynb` — visualize distributions, detect/remove outliers, write `*_no_out.csv`.  
- `demographic_analysis_viz.ipynb` — balance checks (age, tenure, activity, accounts, balances).  
- `hypotesis_testing.ipynb` — confirmatory tests; decisions and CIs.

## 11) Configuration & Parameters
From `config.yaml`: raw input paths, output paths (clean/anomalies/no‑outlier), figures.  
Project parameters: `alpha` (0.05), `diff0` for threshold tests, IQR multiplier `k`, accepted step list, time‑unit (minutes).

## 12) Assumptions & Constraints
- Independent assignment to Control/Test; demographic balance verified in EDA.  
- Web events ordered and UTC‑normalized.  
- Each `(client_id, visitor_id, visit_id)` = one funnel attempt.  
- Period: 2017‑03‑15 → 2017‑06‑20.

## 13) Non‑Functional Requirements
- Reproducibility; traceability (anomalies stored); performance (groupby‑friendly); Pseudonymous IDs only.

## 14) Validation & Acceptance Criteria
- Canonical steps; anomaly rate reported.  
- EDA balance acceptable.  
- KPIs per group with CIs.  
- Hypothesis testing decisions on lift, threshold, errors, and time.  
- Deliverables: CSVs, plots, executive summary.

## 15) Risks & Mitigations
- Allocation bias; skewed times; multiple testing; session linkage errors.

## 16) Runbook
1) `_main_` → 2) `demographic_analysis_viz` → 3) `vanguard_funnel_kpis_` → 4) `vanguard_funnel_outliers_viz` → 5) `hypotesis_testing`.

## 17) Appendix — Key Helper Functions
- `kpis_from_processes`, `step_dropoff_table`, `two_proportion_ztest`, `welch_t_one_sided`, `stratified_completion_tests`.
