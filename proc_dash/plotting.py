from itertools import product
from textwrap import wrap

import pandas as pd
import plotly.express as px

import proc_dash.utility as util

CMAP = px.colors.qualitative.Bold
STATUS_COLORS = {
    "SUCCESS": CMAP[5],
    "FAIL": CMAP[9],
    "UNAVAILABLE": CMAP[10],
}
HISTO_COLOR = CMAP[0]

# TODO: could use util.PIPE_COMPLETE_STATUS_SHORT_DESC to define below variable instead
PIPELINE_STATUS_ORDER = ["SUCCESS", "FAIL", "UNAVAILABLE"]

# Define margins and title position for plots
LAYOUTS = {
    "margin": {"l": 30, "r": 30, "t": 60, "b": 30},  # margins of chart
    "title": {  # figure title position properties, see https://plotly.com/python/reference/layout/#layout-title
        "yref": "container",
        "xref": "paper",
        "x": 0.5,
        "y": 1,
        "xanchor": "center",
        "yanchor": "top",
        "pad": {"t": 20},
    },
}


def transform_active_data_to_long(data: pd.DataFrame) -> pd.DataFrame:
    return pd.melt(
        data,
        id_vars=util.get_id_columns(data),
        var_name="pipeline_name",
        value_name="pipeline_complete",
    )


def wrap_df_column_values(
    df: pd.DataFrame, column: str, width: int
) -> pd.DataFrame:
    """Wraps string values of a column which are longer than the specified character length."""
    if df[column].dtype == "object":
        df[column] = df[column].map(
            lambda value: "<br>".join(
                wrap(text=value, width=width, break_long_words=False)
            ),
            na_action="ignore",
        )
    return df


def plot_pipeline_status_by_participants(
    data: pd.DataFrame, session_list: list
):
    status_counts = (
        transform_active_data_to_long(data)
        .groupby(["pipeline_name", "pipeline_complete", "session"])
        .size()
        .reset_index(name="participants")
    )

    fig = px.bar(
        status_counts,
        x="session",
        y="participants",
        color="pipeline_complete",
        text_auto=True,
        facet_col="pipeline_name",
        category_orders={
            "pipeline_complete": PIPELINE_STATUS_ORDER,
            "session": session_list,
        },
        color_discrete_map=STATUS_COLORS,
        labels={
            "pipeline_name": "Pipeline",
            "participants": "Participants (n)",
            "pipeline_complete": "Processing status",
            "session": "Session",
        },
        title="All participant pipeline statuses by session",
    )
    # Treat session labels as categorical in plot to avoid a continuous x-axis
    fig.update_xaxes(type="category")
    fig.update_layout(margin=LAYOUTS["margin"], title=LAYOUTS["title"])

    return fig


def plot_pipeline_status_by_records(status_counts: pd.DataFrame):
    fig = px.bar(
        status_counts,
        x="pipeline_name",
        y="records",
        color="pipeline_complete",
        text_auto=True,
        category_orders={
            "pipeline_complete": PIPELINE_STATUS_ORDER,
            "pipeline_name": status_counts["pipeline_name"]
            .drop_duplicates()
            .sort_values(),
        },
        color_discrete_map=STATUS_COLORS,
        labels={
            "pipeline_name": "Pipeline",
            "records": "Records (n)",
            "pipeline_complete": "Processing status",
        },
        title="Pipeline statuses of records matching filter (default: all)",
    )
    fig.update_layout(margin=LAYOUTS["margin"], title=LAYOUTS["title"])

    return fig


def populate_empty_records_pipeline_status_plot(
    pipelines: list, statuses: list
) -> pd.DataFrame:
    """Returns dataframe of counts representing 0 matching records in the datatable, i.e., 0 records with each pipeline status."""
    status_counts = pd.DataFrame(
        list(product(pipelines, statuses)),
        columns=["pipeline_name", "pipeline_complete"],
    )
    status_counts["records"] = 0

    return status_counts


def plot_phenotypic_column_histogram(data: pd.DataFrame, column: str):
    """Returns a histogram of the values of the given column across records in the active datatable."""
    title_fsize = 18
    fig = px.histogram(
        wrap_df_column_values(df=data, column=column, width=30),
        x=column,
        color_discrete_sequence=[HISTO_COLOR],
        text_auto=True,
    )
    fig.update_layout(
        margin=LAYOUTS["margin"],
        title={
            "text": f'Count distribution of "{column}" across records matching filter (default: all)',
            "font": {"size": title_fsize},
            **LAYOUTS["title"],
        },
        bargap=0.1,
    )
    return fig
