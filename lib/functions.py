# Add all the imports needed by the functions in the project here
#================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import re
#================================================================
#
# Library of custom preprocessing functions
#================================================================

# Renames all columns in the DataFrame to a consistent, standardized format—typically lowercase with underscores replacing spaces or special characters. 
# This process ensures uniform column naming, which minimizes errors and simplifies referencing columns throughout data cleaning and analysis workflows.
def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
    return df

# Removes duplicate rows from a DataFrame, retaining the first occurrence. 
# Useful for ensuring data integrity and preventing double counting in analyses.
def drop_duplicates(df: pd.DataFrame, column) -> pd.DataFrame: 
    return df.drop_duplicates(subset=[column])

# Concatenates a list of DataFrames into a single DataFrame, stacking them vertically (row-wise). 
# Essential for merging datasets from similar sources or monthly data splits.
def concat_dataframes(left_df, right_df):
	return pd.concat([left_df,right_df], ignore_index = True)

# Removes all punctuation symbols from a given string. 
# Often used during text preprocessing to standardize and clean up textual data for analysis or NLP.
def remove_all_punctuation(df: pd.DataFrame, columns) -> pd.DataFrame:
    # Replace word/word and word-word with space between words
    pattern_slash = r'\b(\w+)(\-|\/)(\w+)\b'
    for col in columns:
        # Replace word/word and word-word
        df[col] = df[col].apply(lambda x: re.sub(pattern_slash, r'\1 \2', x) if isinstance(x, str) else x)
        # Lowercase, remove extra spaces
        df[col] = df[col].str.lower().str.strip().str.replace(r'\s+', ' ', regex=True)
    
    # Remove remaining punctuation (keep only letters, numbers, spaces) --> Outside the for loop
    df[columns] = df[columns].map(lambda x: re.sub(r'[^A-Za-z0-9 ]+', '', x) if isinstance(x, str) else x)
    return df

# Drops specified columns from a DataFrame, helping reduce dimensionality and focus on relevant variables for analysis
def drop_irrelevant_columns(df: pd.DataFrame, columns) -> pd.DataFrame:
    df_drop_cols = df.drop(columns=columns, axis=1, errors="ignore")
    return df_drop_cols

# Flters a DataFrame to keep only rows where the specified column contains a match to the provided regex pattern (case-insensitive).
# Returns a new DataFrame with matching rows, lowercasing the column before searching.
def filter_by_regex_pattern(df: pd.DataFrame, column, regex_pattern: str) -> pd.DataFrame:
    df[column] = df[column].str.lower()
    mask = df[column].str.contains(regex_pattern, flags=re.IGNORECASE, na=False, regex=True)
    return df[mask].copy().reset_index(drop=True)

# Converts specified columns to pandas `datetime` objects. 
# Facilitates time-series analysis, filtering, and date-based grouping.
def standardize_dates(df: pd.DataFrame, date_format_map: dict) -> pd.DataFrame:
    for col, fmt in date_format_map.items():
        # Try strict format first
        try:
            df[col] = pd.to_datetime(df[col], format=fmt, errors='coerce')
        except Exception:
            # Fallback: try default pandas parsing
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


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
