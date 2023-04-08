import pandas as pd
import plotly.express as px

STATUS_CMAP = px.colors.qualitative.Bold
STATUS_COLORS = {
    "SUCCESS": STATUS_CMAP[5],
    "FAIL": STATUS_CMAP[9],
    "INCOMPLETE": STATUS_CMAP[3],
    "UNAVAILABLE": STATUS_CMAP[10],
}
PIPELINE_STATUS_ORDER = ["SUCCESS", "FAIL", "INCOMPLETE", "UNAVAILABLE"]
LAYOUTS = {
    "margin": {"l": 30, "r": 30, "t": 60, "b": 30},  # margins of chart
    "title": {  # figure title position properties
        "yref": "container",
        "y": 1,
        "yanchor": "top",
        "pad": {"t": 20},
    },
}


def plot_pipeline_status_by_participants(data: pd.DataFrame):
    long_data = pd.melt(
        data,
        id_vars=["participant_id", "session"],
        var_name="pipeline_name",
        value_name="pipeline_complete",
    )
    status_counts = (
        long_data.groupby(["pipeline_name", "pipeline_complete", "session"])
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
        category_orders={"pipeline_complete": PIPELINE_STATUS_ORDER},
        color_discrete_map=STATUS_COLORS,
        labels={
            "pipeline_name": "Pipeline",
            "participants": "Participants (n)",
            "pipeline_complete": "Processing status",
            "session": "Session",
        },
        title="Overview: Participant pipeline statuses by session",
    )
    # Treat session labels as categorical in plot to avoid a continuous x-axis
    fig.update_xaxes(type="category")
    fig.update_layout(margin=LAYOUTS["margin"], title=LAYOUTS["title"])

    return fig


def plot_pipeline_status_by_records(data: pd.DataFrame):
    long_data = pd.melt(
        data,
        id_vars=["participant_id", "session"],
        var_name="pipeline_name",
        value_name="pipeline_complete",
    )
    status_counts = (
        long_data.groupby(["pipeline_name", "pipeline_complete"])
        .size()
        .reset_index(name="records")
    )

    fig = px.bar(
        status_counts,
        x="pipeline_name",
        y="records",
        color="pipeline_complete",
        text_auto=True,
        category_orders={"pipeline_complete": PIPELINE_STATUS_ORDER},
        color_discrete_map=STATUS_COLORS,
        labels={
            "pipeline_name": "Pipeline",
            "records": "Records (n)",
            "pipeline_complete": "Processing status",
        },
        title="Selected sessions: Pipeline statuses of matching records (default: all)"
        # alternative title: "Pipeline statuses of unique records for selected sessions (default: all)"
    )
    fig.update_layout(margin=LAYOUTS["margin"], title=LAYOUTS["title"])

    return fig
