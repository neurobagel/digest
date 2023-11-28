import base64
import io
import json
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import pandas as pd

SCHEMAS_PATH = Path(__file__).absolute().parents[1] / "schemas"
BAGEL_CONFIG = {
    "imaging": {
        "schema_file": "bagel_schema.json",
        "overview_col": "pipeline_complete",
    },
    "phenotypic": {
        "schema_file": "bagel_schema_pheno.json",
        "overview_col": "assessment_score",
    },
}
PIPE_COMPLETE_STATUS_SHORT_DESC = {
    "SUCCESS": "All stages of pipeline finished successfully (all expected output files present).",
    "FAIL": "At least one stage of the pipeline failed.",
    "UNAVAILABLE": "Pipeline has not yet been run (output directory not available).",
}


def reset_column_dtypes(data: pd.DataFrame) -> pd.DataFrame:
    """
    Infer more appropriate dtypes for dataframe columns by re-reading in the data.
    This is useful when columns have been formed from splitting a column with mixed dtypes.
    """
    # See https://stackoverflow.com/a/38213524
    stream = io.StringIO()
    data.to_csv(stream, index=False)
    stream.seek(0)
    data_retyped = pd.read_csv(stream)
    stream.close()

    # Just in case, convert session labels back to strings (will avoid sessions being undesirably treated as continuous data in e.g., plots)
    data_retyped["session"] = data_retyped["session"].astype(str)
    return data_retyped


def construct_legend_str(status_desc: dict) -> str:
    """From a dictionary, constructs a legend-style string with multiple lines in the format of key: value."""
    return "\n".join(
        [f"{status}: {desc}" for status, desc in status_desc.items()]
    )


def construct_summary_str(data: pd.DataFrame) -> str:
    """Creates summary of key counts for dataset."""
    return f"""Total number of participants: {count_unique_subjects(data)}
Total number of unique records (participant-session pairs): {count_unique_records(data)}
Total number of unique sessions: {data["session"].nunique()}"""


def get_required_bagel_columns(schema_file: str) -> list:
    """Returns names of required columns from the bagel schema."""
    with open(SCHEMAS_PATH / schema_file, "r") as file:
        schema = json.load(file)

    required_columns = []
    for col_category, cols in schema.items():
        for col, props in cols.items():
            if props["IsRequired"]:
                required_columns.append(col)

    return required_columns


# TODO: When possible values per column have been finalized (waiting on mr_proc),
# validate that each column only has acceptable values
def get_missing_required_columns(bagel: pd.DataFrame, schema_file: str) -> set:
    """Identifies any missing required columns in bagel schema."""
    return set(get_required_bagel_columns(schema_file)).difference(
        bagel.columns
    )


def get_event_id_columns(bagel: pd.DataFrame, schema: str) -> Union[list, str]:
    """Returns names of columns which identify a unique assessment or processing pipeline."""
    if schema == "imaging":
        return ["pipeline_name", "pipeline_version"]
    elif schema == "phenotypic":
        return (
            ["assessment_name", "assessment_version"]
            if "assessment_version" in bagel.columns
            else "assessment_name"
        )


def extract_pipelines(bagel: pd.DataFrame, schema: str) -> dict:
    """Get data for each unique pipeline in the aggregate input as an individual labelled dataframe."""
    pipelines_dict = {}

    # TODO: Possibly temporary fix - to avoid related assessment columns from being out of order
    sort = bool(schema == "imaging")

    groupby = get_event_id_columns(bagel, schema)
    # We only want to sort columns (when needed), not the values inside them. .groupby(sort=True) achieves this
    pipelines = bagel.groupby(by=groupby, sort=sort)

    if isinstance(groupby, list):
        for (name, version), pipeline in pipelines:
            label = f"{name}-{version}"
            # per pipeline, sort by participant_id (not sorting by session_id here to avoid disrupting chronological order)
            pipelines_dict[label] = (
                pipeline.sort_values(["participant_id"])
                .drop(groupby, axis=1)
                .reset_index(drop=True)
            )
    else:
        for name, pipeline in pipelines:
            # per pipeline, sort by participant_id (not sorting by session_id here to avoid disrupting chronological order)
            pipelines_dict[name] = (
                pipeline.sort_values(["participant_id"])
                .drop(groupby, axis=1)
                .reset_index(drop=True)
            )
            pipelines_dict[name] = reset_column_dtypes(pipelines_dict[name])

    return pipelines_dict


def get_id_columns(data: pd.DataFrame) -> list:
    """Returns names of columns which identify a given participant record"""
    return (
        ["participant_id", "bids_id", "session"]
        if "bids_id" in data.columns
        else ["participant_id", "session"]
    )


def are_subjects_same_across_pipelines(
    bagel: pd.DataFrame, schema: str
) -> bool:
    """Checks if subjects and sessions are the same across pipelines in the input."""
    pipelines_dict = extract_pipelines(bagel, schema)

    pipeline_subject_sessions = []
    for df in pipelines_dict.values():
        # per pipeline, rows are sorted first in case participants/sessions are out of order
        pipeline_subject_sessions.append(
            df.sort_values(get_id_columns(bagel)).loc[:, get_id_columns(bagel)]
        )

    return all(
        pipeline.equals(pipeline_subject_sessions[0])
        for pipeline in pipeline_subject_sessions
    )


def count_unique_subjects(data: pd.DataFrame) -> int:
    return (
        data["participant_id"].nunique()
        if "participant_id" in data.columns
        else 0
    )


def count_unique_records(data: pd.DataFrame) -> int:
    """Returns number of unique participant-session pairs."""
    if set(["participant_id", "session"]).issubset(data.columns):
        return data[["participant_id", "session"]].drop_duplicates().shape[0]
    return 0


def get_pipelines_overview(bagel: pd.DataFrame, schema: str) -> pd.DataFrame:
    """
    Constructs a dataframe containing global statuses of pipelines in bagel.csv
    (based on "pipeline_complete" column) for each participant and session.
    """
    pipeline_complete_df = bagel.pivot(
        index=get_id_columns(bagel),
        columns=get_event_id_columns(bagel, schema),
        values=BAGEL_CONFIG[schema]["overview_col"],
    )

    if isinstance(get_event_id_columns(bagel, schema), list):
        pipeline_complete_df.columns = [
            # for neatness, rename pipeline-specific columns from "(name, version)" to "{name}-{version}"
            "-".join(tup)
            for tup in pipeline_complete_df.columns.to_flat_index()
        ]

    # preserves original order of appearance if schema == "phenotypic"
    col_order = extract_pipelines(bagel, schema).keys()

    pipeline_complete_df = (
        # Enforce original order of sessions as they appear in input (pivot automatically sorts them)
        pipeline_complete_df.reindex(
            index=bagel["session"].unique(), level="session"
        )
        .reindex(col_order, axis=1)  # reorder assessments/pipelines if needed
        .reset_index()
        .rename_axis(None, axis=1)
    )

    return reset_column_dtypes(pipeline_complete_df)


def parse_csv_contents(
    contents, filename, schema
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Returns contents of a bagel.csv as a dataframe, if no issues detected.

    Returns
    -------
    pd.DataFrame or None
        Dataframe containing contents of the parsed input tabular file.
    str or None
        Informative error raised during parsing of the input, if applicable.
    """
    error_msg = None
    if filename.endswith(".csv"):
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        bagel = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

        if (
            len(
                missing_req_cols := get_missing_required_columns(
                    bagel, BAGEL_CONFIG[schema]["schema_file"]
                )
            )
            > 0
        ):
            error_msg = f"The selected CSV is missing the following required {schema} metadata columns: {missing_req_cols}. Please try again."
        elif not are_subjects_same_across_pipelines(bagel, schema):
            error_msg = "The pipelines in the selected CSV do not have the same number of subjects and sessions. Please try again."
    else:
        error_msg = "Invalid file type. Please upload a .csv file."

    if error_msg is not None:
        return None, error_msg

    bagel["session"] = bagel["session"].astype(str)
    return bagel, None


def filter_records(
    data: pd.DataFrame,
    session_values: list,
    operator_value: str,
    status_values: dict,
) -> pd.DataFrame:
    """
    Returns dataframe filtered for data corresponding to the specified sessions
    and pipeline statuses. The selected operator value only has effect when >=1 session
    has been selected, and determines whether the filter should be applied at the subject level
    (all; all selected sessions should be present, with pipeline statuses of each matching the filter)
    or at the session level (any; any selected session with pipeline statuses matching the filter).

    Note: This functionality is meant to complement the datatable's built-in
    column-wise filtering UI, since the filtering syntax does not readily support
    intuitive queries for multiple specific values in a column, or multi-column queries.
    """
    pipeline_queries = [
        f"`{pipeline}` == {repr(status_value)}"
        for pipeline, status_value in status_values.items()
        if status_value is not None
    ]

    if not session_values:
        query = " and ".join(pipeline_queries)
    elif operator_value == "AND":
        matching_subs = []
        for sub_id, sub in data.groupby("participant_id"):
            if all(
                session in sub["session"].unique()
                for session in session_values
            ):
                if all(
                    not sub.query(
                        " and ".join(
                            [f"session == '{session}'"] + pipeline_queries
                        )
                    ).empty
                    for session in session_values
                ):
                    matching_subs.append(sub_id)
        query = f"participant_id in {matching_subs} and session in {session_values}"
    else:
        if operator_value == "OR":
            query = " and ".join(
                [f"session in {session_values}"] + pipeline_queries
            )

    data = data.query(query)

    return data


def generate_column_summary_str(column: pd.Series) -> str:
    """
    Compute and return summary statistics for a given column as a string.
    For a numerical column, these include the non-missing and missing value counts, mean, standard deviation, min, median, and max.
    For a categorical column, these include the non-missing and missing value counts, number of unique values, and most common value.
    """
    if np.issubdtype(column.dtype, np.number):
        # Define summary stats we don't care about. We ignore 'count' because we recompute this value as a ratio below.
        ignore_stats = ["25%", "75%", "count"]
        summary_stats = (
            column.describe().rename({"50%": "median"}).map("{:.2f}".format)
        )
    else:
        ignore_stats = ["freq", "count"]
        summary_stats = column.describe().rename(
            {"unique": "unique values", "top": "most common value"}
        )

    summary_stats = pd.concat(
        [
            pd.Series(
                {
                    "non-missing values": f"{column.notna().sum()}/{len(column)}",
                    "missing values": f"{column.isna().sum()}/{len(column)}",
                }
            ),
            summary_stats,
        ],
    )

    summary_str = summary_stats.drop(labels=ignore_stats).to_csv(
        header=False, sep="\t"
    )
    return summary_str.replace("\t", ": ")