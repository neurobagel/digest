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
    "SUCCESS": "All expected output files of pipeline are present.",
    "FAIL": "At least one expected output of pipeline is missing.",
    "INCOMPLETE": "Pipeline has not yet been run (output directory not available).",
    "UNAVAILABLE": "Relevant MRI modality for pipeline not available.",
}

# TODO:
# Could also use URLs for "imaging" or "phenotypic" locations if fetching from a remote repo doesn't slow things down too much.
# Note that this would only work for public repos or private repos with a token.
# TODO: move this to a config file?
PUBLIC_DIGEST_FILE_PATHS = {
    "qpn": {
        "name": "Quebec Parkinson Network",
        "imaging": Path(__file__).absolute().parents[2]
        / "nipoppy-qpn"
        / "nipoppy"
        / "digest"
        / "qpn_imaging_availability_digest.csv",
        "phenotypic": Path(__file__).absolute().parents[2]
        / "nipoppy-qpn"
        / "nipoppy"
        / "digest"
        / "qpn_tabular_availability_digest.csv",
    }
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


def type_column_for_dashtable(df_column: pd.Series) -> str:
    """
    Determines the appropriate type for a given column for use in a dash datatable, using Pandas and the column dtype.
    This is needed because dash datatable does not automatically infer column data types, and will treat all columns as 'text' for filtering purposes by default
    (the actual default column type is 'any' if not defined manually).

    See also https://dash.plotly.com/datatable/filtering.

    # TODO:
    # - This is pretty simplistic and mainly to enable easier selection of filtering UI syntax - we might be able to remove this after switch to AG Grid
    # - If needed, in future could support explicitly setting 'datetime' type as well, by applying pd.to_datetime() and catching any errors
    """
    if np.issubdtype(df_column.dtype, np.number):
        return "numeric"
    return "text"


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


def get_event_id_columns(bagel: pd.DataFrame, schema: str) -> Union[str, list]:
    """
    Returns name(s) of columns which identify a unique assessment or processing pipeline.

    When there is only one relevant column, we return a string instead of a list to avoid grouper problems when the column name is used in pandas groupby.
    """
    if schema == "imaging":
        return ["pipeline_name", "pipeline_version"]
    if schema == "phenotypic":
        return (
            ["assessment_name", "assessment_version"]
            if "assessment_version" in bagel.columns
            else "assessment_name"
        )
    return None


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


def get_duplicate_entries(data: pd.DataFrame, subset: list) -> pd.DataFrame:
    """Returns a dataframe containing only duplicate entries in the input data."""
    return data[data.duplicated(subset=subset, keep=False)]


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
    Constructs a wide format dataframe from the long format input file,
    with one row per participant-session pair and one column per event (e.g., pipeline, assessment)
    """
    # When there are duplicate entries for the combination of participant, session, & event, the first occurrence is kept
    pipeline_complete_df = bagel.pivot_table(
        index=get_id_columns(bagel),
        columns=get_event_id_columns(bagel, schema),
        values=BAGEL_CONFIG[schema]["overview_col"],
        aggfunc="first",
        fill_value=None,  # TODO: Revisit this when we have an idea for a better fill value
        dropna=True,
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


def load_file_from_path(
    file_path: Path,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Reads in a CSV file (if it exists) and returns it as a dataframe."""
    if not file_path.exists():
        return None, "File not found."

    bagel = pd.read_csv(file_path)
    return bagel, None


def load_file_from_contents(
    filename: str, contents: str
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Returns contents of an uploaded CSV file as a dataframe."""
    if not filename.endswith(".csv"):
        return None, "Invalid file type. Please upload a .csv file."

    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    bagel = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    return bagel, None


def get_schema_validation_errors(
    bagel: pd.DataFrame, schema: str
) -> Optional[str]:
    """Checks that the input CSV adheres to the schema for the selected bagel type. If not, returns an informative error message as a string."""
    error_msg = None

    # Get the columns that uniquely identify a participant-session's value for an event,
    # to be able to check for duplicate entries before transforming the data to wide format later on
    unique_value_id_columns = get_id_columns(bagel) + (
        get_event_id_columns(bagel, schema)
        if isinstance(get_event_id_columns(bagel, schema), list)
        else [get_event_id_columns(bagel, schema)]
    )

    if (
        len(
            missing_req_cols := get_missing_required_columns(
                bagel, BAGEL_CONFIG[schema]["schema_file"]
            )
        )
        > 0
    ):
        error_msg = f"The selected CSV is missing the following required {schema} metadata columns: {missing_req_cols}. Please try again."
    elif (
        get_duplicate_entries(
            data=bagel, subset=unique_value_id_columns
        ).shape[0]
        > 0
    ):
        # TODO: Switch to warning once alerts are implemented for errors?
        error_msg = f"The selected CSV contains duplicate entries in the combination of: {unique_value_id_columns}. Please double check your input."

    return error_msg


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
