import pandas as pd
import plotly.express as px


def choose_chart(df: pd.DataFrame):
    if df.empty or len(df.columns) < 2:
        return None

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return None

    cols = df.columns.tolist()
    first = cols[0]
    y = numeric_cols[0]

    if {"year", "month"}.issubset(df.columns) and y:
        chart_df = df.copy()
        chart_df["period"] = chart_df["year"].astype(str) + "-" + chart_df["month"].astype(str).str.zfill(2)
        return px.line(chart_df, x="period", y=y, markers=True)

    if first not in numeric_cols and len(df) <= 30:
        return px.bar(df, x=first, y=y)

    if len(numeric_cols) >= 2:
        return px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])

    return None


def explain_result(question: str, df: pd.DataFrame, sql_source: str) -> str:
    if df.empty:
        return "The query ran successfully, but no rows matched the question."

    columns = ", ".join(df.columns.astype(str))
    return (
        f"The system answered the question using {len(df)} result row(s). "
        f"The returned fields are {columns}. SQL generation source: {sql_source}."
    )
