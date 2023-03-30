"""
Constructs Dash app for viewing and filtering statuses of processing pipelines for a given dataset.
App accepts and parses a user-uploaded bagel.csv file (assumed to be generated by mr_proc) as input.
"""

import base64
import io
import json
from pathlib import Path
from typing import Optional, Tuple

import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from dash import Dash, ctx, dash_table, dcc, html

SCHEMAS_PATH = Path(__file__).absolute().parent.parent / "schemas"


def get_required_bagel_columns() -> list:
    """Returns names of required columns from the bagel schema."""
    with open(SCHEMAS_PATH / "bagel_schema.json", "r") as file:
        schema = json.load(file)

    required_columns = []
    for col_category, cols in schema.items():
        for col, props in cols.items():
            if props["IsRequired"]:
                required_columns.append(col)

    return required_columns


# TODO: When possible values per column have been finalized (waiting on mr_proc),
# validate that each column only has acceptable values
def check_required_columns(bagel: pd.DataFrame):
    """Returns error if required columns in bagel schema are missing."""
    missing_req_columns = set(get_required_bagel_columns()).difference(
        bagel.columns
    )

    # TODO: Check if there are any missing values in the `participant_id` column
    if len(missing_req_columns) > 0:
        raise LookupError(
            f"The selected .csv is missing the following required metadata columns: {missing_req_columns}."
        )


def extract_pipelines(bagel: pd.DataFrame) -> dict:
    """Get data for each unique pipeline in the aggregate input as an individual labelled dataframe."""
    pipelines_dict = {}

    pipelines = bagel.groupby(["pipeline_name", "pipeline_version"])
    for (name, version), pipeline in pipelines:
        label = f"{name}-{version}"
        # per pipeline, rows are sorted in case participants/sessions are out of order
        pipelines_dict[label] = (
            pipeline.sort_values(["participant_id", "session"])
            .drop(["pipeline_name", "pipeline_version"], axis=1)
            .reset_index(drop=True)
        )

    return pipelines_dict


def check_num_subjects(bagel: pd.DataFrame):
    """Returns error if subjects and sessions are different across pipelines in the input."""
    pipelines_dict = extract_pipelines(bagel)

    pipeline_subject_sessions = [
        df.loc[:, ["participant_id", "session"]]
        for df in pipelines_dict.values()
    ]

    if not all(
        pipeline.equals(pipeline_subject_sessions[0])
        for pipeline in pipeline_subject_sessions
    ):
        raise LookupError(
            "The pipelines in bagel.csv do not have the same number of subjects and sessions."
        )


def get_overview(bagel: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs a dataframe containing global statuses of pipelines in bagel.csv
    (based on "pipeline_complete" column) for each participant and session.
    """
    check_required_columns(bagel)
    check_num_subjects(bagel)

    pipeline_complete_df = bagel.pivot(
        index=["participant_id", "session"],
        columns=["pipeline_name", "pipeline_version"],
        values="pipeline_complete",
    )
    pipeline_complete_df.columns = [
        # for neatness, rename pipeline-specific columns from "(name, version)" to "{name}-{version}"
        "-".join(tup)
        for tup in pipeline_complete_df.columns.to_flat_index()
    ]
    pipeline_complete_df.reset_index(inplace=True)

    return pipeline_complete_df


app = Dash(
    __name__,
    external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"],
)


app.layout = html.Div(
    children=[
        html.H2(children="Neuroimaging Derivatives Status Dashboard"),
        dcc.Upload(
            id="upload-data",
            children=html.Button("Drag and Drop or Select .csv File"),
            style={"margin-top": "10px", "margin-bottom": "10px"},
            multiple=False,
        ),
        html.Div(
            id="output-data-upload",
            children=[
                html.H6(id="input-filename"),
                html.Div(
                    children=[
                        html.Div(id="total-participants"),
                        html.Div(
                            id="matching-participants",
                            style={"margin-left": "15px"},
                        ),
                    ],
                    style={"display": "inline-flex"},
                ),
                dash_table.DataTable(
                    id="interactive-datatable",
                    data=None,
                    sort_action="native",
                    sort_mode="multi",
                    filter_action="native",
                    page_size=10,
                ),  # TODO: Treat all columns as strings to standardize filtering syntax?
            ],
            style={"margin-top": "10px", "margin-bottom": "10px"},
        ),
        dbc.Card(
            [
                # TODO: Put label and dropdown in same row
                html.Div(
                    [
                        dbc.Label("Filter by multiple sessions:"),
                        dcc.Dropdown(
                            id="session-dropdown",
                            options=[],
                            multi=True,
                            placeholder="Select one or more available sessions to filter by",
                            # TODO: Can set `disabled=True` here to prevent any user interaction before file is uploaded
                        ),
                    ]
                ),
                html.Div(
                    [
                        dbc.Label("Selection operator:"),
                        dcc.Dropdown(
                            id="select-operator",
                            options=[
                                {
                                    "label": "AND",
                                    "value": "AND",
                                    "title": "Show only participants with all selected sessions.",
                                },
                                {
                                    "label": "OR",
                                    "value": "OR",
                                    "title": "Show participants with any of the selected sessions.",
                                },
                            ],
                            value="AND",
                            clearable=False,
                            # TODO: Can set `disabled=True` here to prevent any user interaction before file is uploaded
                        ),
                    ]
                ),
            ]
        ),
    ]
)


def count_unique_subjects(data: pd.DataFrame) -> int:
    return (
        data["participant_id"].nunique()
        if "participant_id" in data.columns
        else 0
    )


def parse_csv_contents(
    contents, filename
) -> Tuple[
    Optional[pd.DataFrame], Optional[int], Optional[list], Optional[str]
]:
    """
    Returns
    -------
    pd.DataFrame or None
        Dataframe containing global statuses of pipelines for each participant-session.
    int or None
        Total number of unique participants in the dataframe.
    list or None
        List of the unique session ids in the dataset.
    str or None
        Error raised during parsing of the input, if applicable.
    """
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    error_msg = None
    try:
        if ".csv" in filename:
            bagel = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            overview_df = get_overview(bagel=bagel)
            total_subjects = count_unique_subjects(overview_df)
            sessions = overview_df["session"].sort_values().unique().tolist()
        else:
            error_msg = "Input file is not a .csv file."
    except LookupError as err:
        error_msg = str(err)
    except Exception as exc:
        print(exc)
        error_msg = "Something went wrong while processing this file."

    if error_msg is not None:
        return None, None, None, error_msg

    return overview_df, total_subjects, sessions, None


def filter_by_sessions(
    data: pd.DataFrame, session_values: list, operator_value: str
) -> pd.DataFrame:
    """
    Returns dataframe filtered for data corresponding to the specified sessions,
    for participants who have either any or all of the selected sessions, depending
    on the selected operator.

    Note: This functionality is meant to complement the datatable's built-in
    column-wise filtering UI, since the filtering syntax does not readily support
    intuitive queries for multiple specific values in a column.
    """
    if operator_value == "AND":
        matching_subs = []
        for sub_id, sub in data.groupby("participant_id"):
            if all(
                value in sub["session"].unique() for value in session_values
            ):
                matching_subs.append(sub_id)
        data = data[
            data["participant_id"].isin(matching_subs)
            & data["session"].isin(session_values)
        ]
    else:
        if operator_value == "OR":
            data = data[data["session"].isin(session_values)]

    return data


@app.callback(
    [
        Output("interactive-datatable", "columns"),
        Output("interactive-datatable", "data"),
        Output("total-participants", "children"),
        Output("session-dropdown", "options"),
    ],
    [
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        Input("session-dropdown", "value"),
        Input("select-operator", "value"),
    ],
)
def update_outputs(contents, filename, session_values, operator_value):
    if contents is None:
        return None, None, "Upload a CSV file to begin.", []

    data, total_subjects, sessions, upload_error = parse_csv_contents(
        contents=contents, filename=filename
    )

    if upload_error is not None:
        return None, None, f"Error: {upload_error} Please try again.", []

    if session_values:
        data = filter_by_sessions(
            data=data,
            session_values=session_values,
            operator_value=operator_value,
        )

    tbl_columns = [{"name": i, "id": i} for i in data.columns]
    tbl_data = data.to_dict("records")
    tbl_total_subjects = f"Total number of participants: {total_subjects}"
    session_opts = [{"label": ses, "value": ses} for ses in sessions]

    return tbl_columns, tbl_data, tbl_total_subjects, session_opts


@app.callback(
    Output("matching-participants", "children"),
    [
        Input("interactive-datatable", "columns"),
        Input("interactive-datatable", "derived_virtual_data"),
    ],
)
def update_matching_participants(columns, virtual_data):
    """
    If the visible data in the datatable changes, update count of
    unique participants shown ("Participants matching query").

    When no filter (built-in or dropdown-based) has been applied,
    this count will be the same as the total number of participants
    in the dataset.
    """
    # calculate participant count for active table as long as datatable columns exist
    if columns is not None and columns != []:
        active_df = pd.DataFrame.from_dict(virtual_data)
        return (
            f"Participants matching query: {count_unique_subjects(active_df)}"
        )

    return ""


@app.callback(
    [
        Output("input-filename", "children"),
        Output("interactive-datatable", "filter_query"),
        Output("session-dropdown", "value"),
    ],
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def reset_table(contents, filename):
    """If file contents change (i.e., new CSV uploaded), reset file name and filter selection values."""
    if ctx.triggered_id == "upload-data":
        return f"Input file: {filename}", "", ""

    raise PreventUpdate


if __name__ == "__main__":
    app.run_server(debug=True)
