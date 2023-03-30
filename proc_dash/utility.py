import base64
import io
import json
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

SCHEMAS_PATH = Path(__file__).absolute().parents[1] / "schemas"


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


def get_pipelines_overview(bagel: pd.DataFrame) -> pd.DataFrame:
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
            overview_df = get_pipelines_overview(bagel=bagel)
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
