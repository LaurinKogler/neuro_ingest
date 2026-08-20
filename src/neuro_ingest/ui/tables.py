from __future__ import annotations

import pandas as pd
import streamlit as st


def format_datetime_column(series: pd.Series) -> pd.Series:
    formatted = pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d %H:%M")
    return formatted.fillna(series.astype("string")).fillna("")


def source_columns(dataframe: pd.DataFrame) -> list[str]:
    return [
        column
        for column in dataframe.columns
        if column == "source_file" or column == "path" or column.endswith("_path")
    ]


def display_dataframe(
    dataframe: pd.DataFrame,
    columns: list[str] | None = None,
    rename: dict[str, str] | None = None,
    hide_sources: bool = True,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    display_df = dataframe.copy()
    if columns is not None:
        display_df = display_df[
            [column for column in columns if column in display_df.columns]
        ].copy()
    if hide_sources:
        display_df = display_df.drop(columns=source_columns(display_df), errors="ignore")

    for column in display_df.columns:
        lowered = column.lower()
        if lowered.endswith("date") or lowered.endswith("_time"):
            display_df[column] = format_datetime_column(display_df[column])

    if rename:
        display_df = display_df.rename(columns=rename)
    return display_df


def show_collapsible_table(
    label: str,
    dataframe: pd.DataFrame,
    *,
    expanded: bool = False,
    hide_index: bool = True,
    key: str | None = None,
) -> None:
    with st.expander(f"{label} ({len(dataframe):,} rows)", expanded=expanded):
        st.dataframe(dataframe, width="stretch", hide_index=hide_index, key=key)


def first_value(dataframe: pd.DataFrame, column: str) -> object | None:
    if dataframe.empty or column not in dataframe.columns:
        return None
    values = dataframe[column].dropna()
    if values.empty:
        return None
    return values.iloc[0]
