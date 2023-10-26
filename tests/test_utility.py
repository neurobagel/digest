import numpy as np
import pandas as pd
import pytest

import proc_dash.plotting as plot
import proc_dash.utility as util


@pytest.mark.parametrize(
    "filename",
    ["imagingbagel.tsv", "imagingbagel.txt", "imagingbagel.csv.tsv"],
)
def test_invalid_filetype_returns_informative_error(filename):
    toy_upload_contents = "stand-in for a base64 encoded file contents string"
    bagel, upload_error = util.parse_csv_contents(
        toy_upload_contents, filename, "imaging"
    )

    assert bagel is None
    assert "Invalid file type" in upload_error


def test_reset_column_dtypes():
    """
    Test that reset_column_dtypes() infers more appropriate dtypes for columns whose values were erroneously stored as strings,
    and that the 'session' column is always converted to strings (object dtype).
    """
    pheno_overview_df = pd.DataFrame(
        {
            "participant_id": ["sub-1", "sub-2", "sub-3"],
            "session": [1, 1, 1],
            "group": ["PD", "PD", "PD"],
            "moca_total": ["21", "24", np.nan],
            "moca_total_status": ["true", "true", "false"],
        }
    )

    pheno_overview_df_retyped = util.reset_column_dtypes(pheno_overview_df)

    assert pheno_overview_df_retyped["participant_id"].dtype == "object"
    assert pheno_overview_df_retyped["session"].dtype == "object"
    assert pheno_overview_df_retyped["group"].dtype == "object"
    assert pheno_overview_df_retyped["moca_total"].dtype == "float64"
    assert pheno_overview_df_retyped["moca_total_status"].dtype == "bool"


def test_wrap_df_column_values():
    """Test that wrap_df_column_values() wraps values of a column which are longer than the specified length."""
    df = pd.DataFrame(
        {
            "updrs_p3_hy": [
                "Stage 0: Asymptomatic",
                "Stage 1: Unilateral involvement only",
                "Stage 2: Bilateral involvement without impairment of balance",
            ]
        }
    )
    wrapped_df = plot.wrap_df_column_values(df, "updrs_p3_hy", 30)
    assert all("<br>" in value for value in wrapped_df["updrs_p3_hy"][1:3])
    assert "<br>" not in wrapped_df["updrs_p3_hy"][0]


@pytest.mark.parametrize(
    "column,nonmissing,missing,stats",
    [
        ("group", "3/3", "0/3", ["unique values", "most common value"]),
        ("moca_total", "2/3", "1/3", ["mean", "std", "min", "median", "max"]),
        (
            "moca_total_status",
            "3/3",
            "0/3",
            ["mean", "std", "min", "median", "max"],
        ),
    ],
)
def test_generate_column_summary_str(column, nonmissing, missing, stats):
    """Test that generate_column_summary_str() returns a string with the correct summary statistics for a given column."""
    pheno_overview_df = pd.DataFrame(
        {
            "participant_id": ["sub-1", "sub-2", "sub-3"],
            "session": [
                "1",
                "1",
                "1",
            ],  # the session column is always converted to strings for the dashboard
            "group": ["PD", "PD", "PD"],
            "moca_total": [21, 24, np.nan],
            "moca_total_status": [True, True, False],
        }
    )
    column_summary = util.generate_column_summary_str(
        pheno_overview_df[column]
    )

    assert [stat in column_summary for stat in stats]
    assert f"non-missing values: {nonmissing}" in column_summary
    assert f"missing values: {missing}" in column_summary
