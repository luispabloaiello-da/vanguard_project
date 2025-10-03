1. Dataset Exploration & Initial Data Cleaning

a. Dataset Overview
- df_demo: Client demographics (age, gender, tenure, balance, etc.)
- df_exp_clients: A/B test group assignment (Test/Control/NaN)
- df_web_data_pt_1 & pt_2: Digital footprint (web steps & timestamps, to be merged)

b. Data Cleaning
Check for:

- Missing values
- Duplicates
- Inconsistent or unexpected values (e.g., 'gendr' has 'U', 'X', nulls).
- Mismatches between client lists (e.g., experiment clients not in demo data)

c. Merge Datasets
- Merge df_web_data_pt_1 and df_web_data_pt_2 into a single df_web_data.
- For later analysis, you’ll need to join client demographic data with experiment assignment and web activity.

2. Client Demographics Analysis

a. Who Are the Primary Clients?

Use plots and stats to answer:

Age Distribution:
- Already explored: mean ≈ 46.4, median ≈ 47, mode ≈ 58.5, SD ≈ 15.6 (Clients are typically middle-aged, but with a wide spread)
- Quartiles: Q1 (youngest) to Q4 (oldest), each ≈ 17–18k clients
- Plot: Histogram and boxplot of age (already done)
Gender Distribution:
- Unique values: ['U', 'M', 'F', NaN, 'X']
- Frequency count for each gender code (use df_demo['gendr'].value_counts(dropna=False))
Tenure:
- Distribution of clnt_tenure_yr and clnt_tenure_mnth (new vs. long-standing)
- Plot: Histogram or boxplot of tenure in years
Other variables: Number of accounts, balances, logons/calls (can give extra behavioral context)

b. Age & Tenure Relationship
- Cross-tab age quantiles with tenure quantiles (Are younger clients newer? Are older clients more tenured?)
- Plot: Scatter or heatmap (age vs. tenure)
- Calculate correlation between age and tenure

c. Are They Younger/Older, New/Long-standing?
- Summarize the findings from above:
-- Are most clients in the middle/upper age quartiles?
-- What is their median tenure?
-- Are new clients (low tenure) mostly younger/older than average?

3. Client Behavior Analysis

Beyond the demographics, look for:

Engagement:
- Distribution of logons and calls in last 6 months
- Are more engaged clients (more logons/calls) older/younger, or new/long-standing?
Balance:
- Are higher-balance clients more likely to be older/long-standing?
- Plot: Balance by age and tenure

4. Recommended Outputs & Visuals

- Age and tenure histograms/boxplots
- Gender distribution bar chart
- Cross-tab or heatmap: Age vs. Tenure
- Table: Summary statistics for age, tenure, engagement, balance
- Brief markdown summary for each plot/table