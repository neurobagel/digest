import base64
import io
import json
from pathlib import Path
from typing import Union

import pandas as pd
from dash.dependencies import Input, Output, State

from dash import Dash, dash_table, dcc, html

SCHEMAS_PATH = Path(__file__).absolute().parent.parent / "schemas"


# TODO: When possible values per column have been finalized (waiting on mr_proc),
# validate that each column only has acceptable values
def get_required_bagel_columns() -> list:
    with open(SCHEMAS_PATH / "proc_status_schema.json", "r") as file:
        schema = json.load(file)

    required_columns = []
    for col_category, cols in schema.items():
        for col, props in cols.items():
            if props["IsRequired"]:
                required_columns.append(col)

    return required_columns


def extract_pipelines(bagel: pd.DataFrame) -> dict:
    """Get data for each unique pipeline in the aggregate input as an individual labelled dataframe."""
    missing_req_columns = set(get_required_bagel_columns()).difference(
        bagel.columns
    )

    if len(missing_req_columns) > 0:
        raise LookupError(
            f"Error: The selected .csv is missing the following required metadata columns: {missing_req_columns}"
        )

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


def check_num_subjects(pipelines_dict: dict) -> Union[pd.DataFrame, None]:
    """
    Checks if the subjects and sessions are the same per pipeline in the input.
    Return dataframe with only "participant_id" and "session" columns if true, return None otherwise.
    """
    pipeline_subject_sessions = [
        df.loc[:, ["participant_id", "session"]]
        for df in pipelines_dict.values()
    ]

    if not all(
        pipeline.equals(pipeline_subject_sessions[0])
        for pipeline in pipeline_subject_sessions
    ):
        return None
    else:
        return pipeline_subject_sessions[0]


def get_overview(bagel: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs a dataframe containing global statuses of pipelines in bagel.csv
    (based on "pipeline_complete" column) for each participant and session.
    """

    pipelines_dict = extract_pipelines(bagel)
    pipeline_complete_df = check_num_subjects(pipelines_dict)

    if pipeline_complete_df is None:
        raise LookupError(
            "Error: The pipelines in bagel.csv do not have the same number of subjects and sessions."
        )

    for label, df in pipelines_dict.items():
        pipeline_complete_df[label] = df.loc[:, "pipeline_complete"]

    return pipeline_complete_df


app = Dash(
    __name__,
    external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"],
)

app.layout = html.Div(
    children=[
        html.H1(
            children="NeurDS-dash: Neuroimaging Derivatives Status dashboard"
        ),
        dcc.Upload(
            id="upload-data",
            children=html.Button("Drag and Drop or Select .csv File"),
            style={"margin": "10px"},
            multiple=False,
        ),
        html.Div(id="output-data-upload"),
    ]
)


def parse_contents(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)

    try:
        if ".csv" in filename:
            bagel = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        else:
            return html.Div(
                ["Error: Input file is not a .csv file. Please try again."]
            )
    except Exception as exc:
        print(exc)
        return html.Div(["There was an error processing this file."])

    try:
        return html.Div(
            [
                html.H5("Input file: " + filename),
                dash_table.DataTable(
                    data=get_overview(bagel=bagel).to_dict("records"),
                    page_size=10,
                ),
            ]
        )
    except LookupError as err:
        return html.Div(str(err))


@app.callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)  # TODO: use absolute file path instead?
def update_output(contents, filename):
    if contents is not None:
        children = [parse_contents(contents=contents, filename=filename)]

        return children


if __name__ == "__main__":
    app.run_server(debug=True)
