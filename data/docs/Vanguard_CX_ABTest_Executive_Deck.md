# Vanguard CX Funnel A/B Test — Executive Deck (5 slides)

## Slide 1 — Goal
- Decide whether to ship a new UI based on:
  - Completion lift (primary KPI)
  - Cost-effectiveness threshold: +5 percentage points
  - Error rate and Time-to-complete (no regressions)

## Slide 2 — Experiment & Data
- A/B from 2017-03-15 to 2017-06-20; Control vs redesigned Test UI
- Funnel: Start → Step1 → Step2 → Step3 → Confirm
- Data: demographics, experiment roster, web event logs
- Session features: completion, back-jumps, step times, total time

## Slide 3 — KPIs & Quality
- KPIs: Completion, Error rate, Time (per hop & total), Outcome mix
- Outlier policy: IQR filter; anomalies quarantined with reasons
- Balance checks across age, tenure, activity; Wilson CIs for proportions

## Slide 4 — Statistical Tests & Threshold
- Completion: one-sided 2-proportion z (H1: Test > Control)
- Threshold: z-test with diff0 = 0.05 (H1: lift ≥ +5pp)
- Error rate: one-sided z (H1: Test < Control)
- Time: Welch’s t (H1: Test faster); report Mann–Whitney if non-normal

## Slide 5 — Decision & Next Steps
- Ship if lift is significant and ≥ +5pp with no regressions
- Stratified checks (age, tenure, device/channel if available)
- If borderline: iterate UI at largest drop-off; re-test with power calc
- Package pipeline as CLI/cron; monitor post-launch KPIs & alerting
