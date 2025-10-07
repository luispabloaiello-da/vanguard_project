# Pseudocode (Simplified) for `vanguard_funnel_kpis_.ipynb`
# Style inspired by the temperature conversion exercise pseudocode.
# Goal: Describe in plain, beginner‑friendly steps what the notebook does.

# ================================================================
# 0. IMPORTS & CONFIG
# ================================================================
# 1. Import Python libraries (yaml, pandas, numpy, datetime, plotting, stats, etc.)
# 2. Try to open a YAML config file (../config.yaml). If not found, print a warning.
# 3. Read 3 CSVs from config:
#       - df_demo_test: demographic + flag data for TEST group
#       - df_demo_control: demographic + flag data for CONTROL group
#       - df_web_data: raw web event log (all steps, all users)
# 4. (Optional future step) Could import custom helper functions (currently commented out)

# ================================================================
# 1. DEFINE GLOBAL CONSTANTS & SMALL HELPERS
# ================================================================
# 5. Define ordered list of funnel steps: ['start','step_1','step_2','step_3','confirm']
# 6. Make a dictionary STEP_MAP that maps each step name → numeric index
# 7. Define KEY list = ['client_id','visitor_id','visit_id'] (these uniquely identify a process)
# 8. Define a helper _to_utc(series):
#       - Convert strings to datetimes
#       - Localize or convert to UTC timezone
# 9. Define a helper _standardize_steps(df):
#       - Lowercase step names, strip spaces, normalize to canonical names
#       - Keep only rows where process_step is one of the allowed funnel steps

# ================================================================
# 2. PREPARE WEB DATA PER GROUP
# ================================================================
# 10. Function prepare_web_for_group(df_web_data, df_demo_group):
#       a. Get list of client_ids for that group
#       b. Filter web events to those client_ids
#       c. Standardize step names
#       d. Convert timestamps to UTC
#       e. Sort rows by KEY + timestamp
#       f. Return cleaned web events for that group

# ================================================================
# 3. DETECT STEP BACKS
# ================================================================
# 11. Function compute_back_jumps(w_full):
#       a. Map each row’s step to numeric index (step_idx)
#       b. For each process (grouped by KEY) compute previous step index
#       c. delta = current_step_idx - prev_step_idx
#       d. Flag is_back_jump if delta < 0 (means user moved backward)
#       e. Aggregate number of back jumps per process (sum)
#       f. Return:
#            - wf: detailed events with step indices and back-jump flags
#            - back: table (one row per process) with count of back jumps

# ================================================================
# 4. KEEP ONLY LAST OCCURRENCE OF EACH STEP
# ================================================================
# 12. Function collapse_last_per_step_and_last_confirm(wf):
#       a. If multiple 'confirm' events exist in a process, keep only the last one
#       b. Sort by KEY + process_step + time
#       c. Drop all but the LAST occurrence of each step per process
#       d. Return this condensed table (one row per step per process)

# ================================================================
# 5. SUMMARIZE PROCESSES INTO ONE ROW EACH
# ================================================================
# 13. Function summarize_processes(wf2, back):
#       a. Pivot timestamps so each process has columns for each step time
#       b. Ensure missing steps become NaT (missing timestamp)
#       c. Convert all datetimes to naive UTC (remove timezone)
#       d. Create binary reached_* flags (1 if timestamp exists, else 0)
#       e. completed = reached_confirm
#       f. Compute time differences (minutes) between:
#            - start → step_1
#            - step_1 → step_2
#            - step_2 → step_3
#            - step_3 → confirm
#            - start → confirm (total)
#       g. Join in back-jump counts
#       h. Define outcome:
#            - "successful" if completed AND no back jumps
#            - "completed_with_errors" if completed AND back jumps > 0
#            - "fail" if not completed
#       i. Return one-row-per-process table with flags, times, outcome

# ================================================================
# 6. CALCULATE KPIs
# ================================================================
# 14. Function kpis_from_processes(proc):
#       a. Denominator = number of processes that “started” (reached_start)
#       b. Compute percent reaching each step (step_1, step_2, step_3)
#       c. Compute completion_rate_% (confirm reached)
#       d. Compute distribution of outcomes (successful, completed_with_errors, fail)
#       e. Compute median times between each transition + total
#       f. Compute average number of back jumps
#       g. Return a one-row DataFrame with KPI values

# 15. Function step_dropoff_table(proc):
#       a. For each step transition (start→step_1, step_1→step_2, etc.):
#            - n_from = number of processes that reached the “from” step
#            - n_to   = number that reached the “to” step
#            - conv_rate_% = (n_to / n_from)*100
#            - dropoff_%   = 100 - conv_rate_%
#       b. Return a table describing funnel conversion and drop-off rates

# ================================================================
# 7. REMOVE INCONSISTENT / IMPOSSIBLE SEQUENCES
# ================================================================
# 16. Function _starnger_things(proc_df):
#       a. Ensure required reached_* columns exist; create if missing
#       b. Build rules that mark anomalies (e.g., reached step_2 without step_1)
#       c. Combine anomaly flags into one mask
#       d. Tag reason text for each anomaly
#       e. Split into:
#            - proc_clean (valid sequences)
#            - proc_anomalies (invalid / inconsistent)
#       f. Return both (clean, anomalies)

# ================================================================
# 8. RUN PIPELINE FOR CONTROL GROUP
# ================================================================
# 17. w_control = prepare_web_for_group(df_web_data, df_demo_control)
# 18. wf_control, back_control = compute_back_jumps(w_control)
# 19. wf2_control = collapse_last_per_step_and_last_confirm(wf_control)
# 20. proc_control = summarize_processes(wf2_control, back_control)
# 21. proc_control_clean, proc_control_anomalies = _starnger_things(proc_control)
# 22. kpis_control = kpis_from_processes(proc_control_clean)
# 23. dropoff_control = step_dropoff_table(proc_control_clean)
# 24. Display:
#       - First rows of cleaned process table
#       - KPI summary
#       - Step drop-off
#       - Counts of valid vs anomalies
#       - Distinct control clients
#       - Sample individual client process rows (sanity checks)

# ================================================================
# 9. RUN PIPELINE FOR TEST GROUP
# ================================================================
# 25. w_test = prepare_web_for_group(df_web_data, df_demo_test)
# 26. wf_test, back_test = compute_back_jumps(w_test)
# 27. wf2_test = collapse_last_per_step_and_last_confirm(wf_test)
# 28. proc_test = summarize_processes(wf2_test, back_test)
# 29. proc_test_clean, proc_test_anomalies = _starnger_things(proc_test)
# 30. kpis_test = kpis_from_processes(proc_test_clean)
# 31. dropoff_test = step_dropoff_table(proc_test_clean)
# 32. Display:
#       - First rows of cleaned process table
#       - KPI summary
#       - Step drop-off
#       - Counts of valid vs anomalies
#       - Distinct test clients
#       - Sample individual client rows (sanity checks)

# ================================================================
# 10. SAVE RESULTS
# ================================================================
# 33. Save cleaned control process table to CSV (file6)
# 34. Save cleaned test process table to CSV (file7)

# ================================================================
# 11. (NOT PRESENT BUT NEXT STEPS COULD BE)
# ================================================================
# 35. Combine control + test for statistical tests (e.g., completion rate comparison)
# 36. Perform hypothesis testing (not in this notebook yet)
# 37. Produce visualizations (funnel charts, time distributions)
# 38. Generate final report / executive summary

# END OF PSEUDOCODE