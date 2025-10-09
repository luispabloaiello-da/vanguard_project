# Add all the imports needed by the functions in the project here
#================================================================
import yaml
import datetime as dt
import re
import pandas as pd
import scipy.stats as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import statsmodels.api as sm
import seaborn as sns

from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.multivariate.manova import MANOVA
from scipy import stats
from scipy.stats import pearsonr, boxcox, chi2_contingency, shapiro, probplot
from scipy.stats.contingency import association
#================================================================
#
# Library of custom preprocessing functions
#================================================================

# ========= KPIs & Drop-off =========
def kpis_from_processes(proc: pd.DataFrame) -> pd.DataFrame:
    d = proc.copy()
    denom = max(1, int(d['reached_start'].sum()))   # who started

    kpis = {
        'n_processes'          : int(len(d)),
        'started'              : int(d['reached_start'].sum()),
        'step1_rate_%'         : 100*d['reached_step_1'].sum()/denom,
        'step2_rate_%'         : 100*d['reached_step_2'].sum()/denom,
        'step3_rate_%'         : 100*d['reached_step_3'].sum()/denom,
        'completion_rate_%'    : 100*d['completed'].sum()/denom,
        'successful_%'              : 100*(d['outcome'].eq('successful').sum())/denom,
        'completed_with_errors_%'   : 100*(d['outcome'].eq('completed_with_errors').sum())/denom,
        'fail%'                     : 100*(d['outcome'].eq('fail').sum())/denom,
        't_total_avg_min'   : float(np.nanmean(d['t_total'])),
        # 't_total_median_min'   : float(np.nanmedian(d['t_total'])),
        't_step1_avg_min'   : float(np.nanmean(d['t_start_step1'])),
        # 't_step1_median_min'   : float(np.nanmedian(d['t_start_step1'])),
        't_step2_avg_min'   : float(np.nanmean(d['t_step1_step2'])),
        # 't_step2_median_min'   : float(np.nanmedian(d['t_step1_step2'])),
        't_step3_avg_min'   : float(np.nanmean(d['t_step2_step3'])),
        # 't_step3_median_min'   : float(np.nanmedian(d['t_step2_step3'])),
        't_conf_avg_min'    : float(np.nanmean(d['t_step3_conf'])),
        # 't_conf_median_min'    : float(np.nanmedian(d['t_step3_conf'])),
        'n_back_jumps'       : int(d['n_back_jumps'].sum()),
        'avg_back_jumps'       : float(d['n_back_jumps'].mean())
    }
    return pd.DataFrame([kpis])

#

def step_dropoff_table(proc: pd.DataFrame) -> pd.DataFrame:
    d = proc.copy()
    rows = [
        ("start→step_1", int(d['reached_start'].sum()),   int(d['reached_step_1'].sum())),
        ("step_1→step_2", int(d['reached_step_1'].sum()), int(d['reached_step_2'].sum())),
        ("step_2→step_3", int(d['reached_step_2'].sum()), int(d['reached_step_3'].sum())),
        ("step_3→confirm", int(d['reached_step_3'].sum()), int(d['completed'].sum())),
    ]
    out = pd.DataFrame(rows, columns=['from_to','n_from','n_to'])
    out['conv_rate_%'] = 100 * out['n_to'] / out['n_from'].replace({0:np.nan})
    out['conv_rate_%'] = out['conv_rate_%'].fillna(0.0)
    out['dropoff_%'] = 100 - out['conv_rate_%']
    return out

## PROPORTION TESTS

def two_proportion_ztest(x1, n1, x2, n2, *, alternative='larger', diff0=0.05, alpha=0.05):
    """
    One-sided two-proportion z-test (TEST vs CONTROL).

    Parameters
    ----------
    x1 : Number of "successes" in TEST (e.g., completed).
    n1 : Number of trials in TEST (e.g., started).
    x2 : Number of "successes" in CONTROL.
    n2 : Number of trials in CONTROL.
    alternative : {'larger','smaller','two-sided'}, default 'larger'
        Direction of H1. By convention, p1 is TEST, p2 is CONTROL:
          - 'larger'  → H1: p1 - p2 > diff0  (TEST > CONTROL)
          - 'smaller' → H1: p1 - p2 < diff0  (TEST < CONTROL)
          - 'two-sided' → H1: p1 - p2 ≠ diff0
    diff0 : float, default 0.05
        Null difference p1 - p2 under H0 (use 0.0 for no-lift; 0.05 for ≥5pp lift test).
    alpha : float, default 0.05
        Significance level for reporting confidence intervals (CIs).

    Returns
    -------
    dict with:
      z_stat, p_value, p_test, p_control, diff, null_diff,
      ci_test (Wilson), ci_control (Wilson),
      n_test, x_test, n_control, x_control, alternative
    """
    count  = np.array([x1, x2], dtype=float)    # successes
    nobs   = np.array([n1, n2], dtype=float)    # trials
    #z = ((p_test - p_ctrl) - 0.05) / np.sqrt( p(1-p) *((1/n1 + (1/n2))))
    z, p   = proportions_ztest(count, nobs, value=diff0, alternative=alternative)
    phat1, phat2 = count / nobs
    # 95% CIs for each proportion (Wilson)
    ci1 = proportion_confint(count[0], nobs[0], alpha=alpha, method="wilson")
    ci2 = proportion_confint(count[1], nobs[1], alpha=alpha, method="wilson")
    return {
        'z_stat': float(z),
        'p_value': float(p),
        'p_test': float(phat1),
        'p_control': float(phat2),
        'diff': float(phat1 - phat2),
        'null_diff': float(diff0),
        'ci_test': tuple(map(float, ci1)),
        'ci_control': tuple(map(float, ci2)),
        'n_test': int(n1), 'x_test': int(x1),
        'n_control': int(n2), 'x_control': int(x2),
        'alternative': alternative
    }

# MEAN TESTS

def welch_t_one_sided(x_test, x_ctrl, *, alternative='less'):
    """
    Welch's t-test (one-sided).
    alternative='less' encodes H1: mean(x_test) < mean(x_ctrl).
    Returns: {'w_stat': t-statistic, 'p_value': p-value, 'n_test': used N in test, 'n_ctrl': used N in control}
    """

    # Ensure both inputs are numeric arrays/Series;
    # non-numeric values are coerced to NaN so they can be ignored by the test.
    x = pd.to_numeric(x_test, errors='coerce')
    y = pd.to_numeric(x_ctrl, errors='coerce')

    # Run Welch’s two-sample t-test (does NOT assume equal variances).
    # nan_policy='omit' drops NaNs; 'alternative' sets the tail:
    #   'less'   → H1: mean(x) < mean(y)
    #   'greater'→ H1: mean(x) > mean(y)
    #   'two-sided' → H1: means are different
    res = st.ttest_ind(x, y, equal_var=False, nan_policy='omit', alternative=alternative)

    # Package results:
    # - statistic: the t value
    # - pvalue: one-sided p-value given 'alternative'
    # - n_test / n_ctrl: number of non-NaN observations used in each group
    return {
        'w_stat': float(res.statistic),
        'p_value': float(res.pvalue),
        'n_test': int(x.notna().sum()),
        'n_ctrl': int(y.notna().sum())
    }

#

def stratified_completion_tests(T, C, by_col, alpha=0.05):
    rows = []
    for level in sorted(set(T[by_col].dropna()) | set(C[by_col].dropna())):
        Ct = C[C[by_col]==level]; Tt = T[T[by_col]==level]
        n_c, x_c = int(Ct['reached_start'].sum()), int(Ct['completed'].sum())
        n_t, x_t = int(Tt['reached_start'].sum()), int(Tt['completed'].sum())
        if n_c == 0 or n_t == 0: 
            rows.append({'level':level,'n_test':n_t,'n_ctrl':n_c,'z':np.nan,'p':np.nan,'diff':np.nan}); 
            continue
        res = two_proportion_ztest(x_t, n_t, x_c, n_c, diff0=0.5, alternative='larger', alpha=alpha)
        rows.append({'level':level, 'n_test':res['n_test'], 'n_control':res['n_control'],
                    'p_test':res['p_test'], 'p_control':res['p_control'], 'diff':res['diff'],
                    'z_stat':res['z_stat'], 'p_value':res['p_value']})
    return pd.DataFrame(rows)

#

def decision_line(name, p, alpha=0.05, h1_text="TEST better than CONTROL"):
    print(f"{name}: p={p:.4g} → " + ("Reject H0; " + h1_text if p < alpha else "Fail to reject H0."))

#

def show_statistical_test(statistic: float, alpha: float, n: int, distribution: str=["t-student","normal"], alternative: str=["two-sided","lower","greater"]):

    if distribution not in ["t-student","normal"]:
        raise TypeError("Sorry, only 't-student', and 'normal' distributions are acepted")

    if alternative not in ["two-sided","lower","greater"]:
        raise TypeError("Sorry, only 'two-sided', 'lower', and 'greated' are acepted valued for the alternative")

    if not isinstance(statistic, float):
        raise TypeError("Sorry, the data type for the statistic must be float")

    if not isinstance(alpha, float):
        raise TypeError("Sorry, the data type for alpha must be float")

    if not isinstance(n, int):
        raise TypeError("Sorry, the data type for n must be int")

    x_values = np.linspace(-3, 3)

    if distribution == "t-student":

        y_values = st.t.pdf(x_values, df=n-1)

        if alternative == "two-sided": # Computing the critical values

            lower_critical_value = st.t.ppf(alpha/2, df=n-1)
            upper_critical_value = st.t.ppf(1-(alpha/2), df=n-1)

            x_values1 = np.linspace(-3, lower_critical_value)
            y_values1 = st.t.pdf(x_values1, df=n-1)

            x_values2 = np.linspace(upper_critical_value, 3)
            y_values2 = st.t.pdf(x_values2, df=n-1)

        elif alternative == "lower":

            critical_value = st.t.ppf(alpha, df=n-1)

            x_values1 = np.linspace(-3, critical_value)
            y_values1 = st.t.pdf(x_values1, df=n-1)

        elif alternative == "greater":

            critical_value = st.t.ppf(1-alpha, df=n-1)

            x_values2 = np.linspace(critical_value, 3)
            y_values2 = st.t.pdf(x_values2, df=n-1)

    elif distribution == "normal":

        y_values = st.norm.pdf(x_values)

        if alternative == "two-sided": # Computing the critical values

            lower_critical_value = st.norm.ppf(alpha/2)
            upper_critical_value = st.norm.ppf(1-(alpha/2))

            x_values1 = np.linspace(-3, lower_critical_value)
            y_values1 = st.norm.pdf(x_values1)

            x_values2 = np.linspace(upper_critical_value, 3)
            y_values2 = st.norm.pdf(x_values2)

        elif alternative == "lower":

            critical_value = st.norm.ppf(alpha)

            x_values1 = np.linspace(-3, critical_value)
            y_values1 = st.norm.pdf(x_values1)

        elif alternative == "greater":

            critical_value = st.norm.ppf(1-alpha)

            x_values2 = np.linspace(critical_value, 3)
            y_values2 = st.norm.pdf(x_values2)

    df = pd.DataFrame({"x": x_values, "pdf": y_values})

    title = f"{distribution} Probability Density Function"

    fig = px.line(df, x="x", y="pdf", title=title)

    if alternative == "two-sided":

        fig.add_vline(x=lower_critical_value, line_color="red")
        fig.add_vline(x=upper_critical_value, line_color="red")

        fig.add_annotation(x=lower_critical_value,y=0,text=f"Lower critical value {lower_critical_value: .2f}",xref="x",yref="paper",yanchor="bottom")
        fig.add_annotation(x=upper_critical_value,y=0,text=f"Upper critical value {upper_critical_value: .2f}",xref="x",yref="paper",yanchor="bottom")

        fig.add_scatter(x=x_values1, y=y_values1,fill='tozeroy', mode='none' , fillcolor='red')
        fig.add_scatter(x=x_values2, y=y_values2,fill='tozeroy', mode='none' , fillcolor='red')

    elif alternative == "lower":

        fig.add_vline(x=critical_value, line_color="red")
        fig.add_annotation(x=critical_value,y=0,text=f"Critical value {critical_value: .2f}",xref="x",yref="paper",yanchor="bottom")

        fig.add_scatter(x=x_values1, y=y_values1,fill='tozeroy', mode='none' , fillcolor='red')

    elif alternative == "greater":

        fig.add_vline(x=critical_value, line_color="red")
        fig.add_annotation(x=critical_value,y=0,text=f"Critical value {critical_value: .2f}",xref="x",yref="paper",yanchor="bottom")

        fig.add_scatter(x=x_values2, y=y_values2,fill='tozeroy', mode='none' , fillcolor='red')

    fig.add_vline(x=statistic)
    fig.add_annotation(x=statistic,y=0,text=f"Statistic {statistic: .2f}",xref="x",yref="paper",yanchor="bottom")

    fig.update_layout(title_text=f'{distribution} Probability Density Function', title_x=0.5)

    fig.update_layout(showlegend=False)

    fig.show()


## def remove_all_punctuation(df: pd.DataFrame, columns) -> pd.DataFrame:
#    df[columns] = df[columns].map(lambda x: re.sub(r'[^A-Za-z0-9 ]+', '', x) if isinstance(x, str) else x)
#    # Lowercase All Categorical/Text Columns and Remove Extra Spaces
#    for col in columns:
#        df[col] = df[col].str.lower().str.strip().str.replace(r'\s+', ' ', regex=True)
#    return df

## def remove_all_punctuation(df: pd.DataFrame, columns) -> pd.DataFrame:
#     for col in columns:
#         df[col] = df[col].apply(
#             lambda x: re.sub(r'[^\w\s]', ' ', x) if isinstance(x, str) else x)  # Replace \ punctuation with space
#         df[col] = df[col].apply(lambda x: re.sub(r'\s+', ' ', x) if isinstance(x, str) else x)  # Remove extra spaces
#         df[col] = df[col].str.lower().str.strip()  # Lowercase & clean spaces
#     return df

# Converts specified columns to pandas `datetime` objects, handling various string date formats. 
# Facilitates time-series analysis, filtering, and date-based grouping.
## def standardize_dates(df: pd.DataFrame, column) -> pd.DataFrame:
#     df[column] = pd.to_datetime(df[column], format="%d-%b-%Y", errors='coerce') # Convert 'post_until' to datetime (with your format)
#     df[column] = df[column].dt.strftime('%d-%m-%Y') # Format 'post_until' as string in 'dd-mm-YYYY'
#     return df

# regex_pattern = r"(sql|tableau|bi|phyton|eda|llm|ai|ml|pandas|NumPy|Agile)"
# # Apply re.findall to each row in the 'Preferred_Skills' column
# keyword_matches = df_merged['Preferred_Skills'].apply(lambda x: re.findall(regex_pattern, x, flags=re.IGNORECASE) if isinstance(x, str) else [])
# # Filter rows where at least one keyword was found
# df_keywords = df_merged[keyword_matches.apply(lambda matches: len(matches) > 0)].copy().reset_index(drop=True)
