import numpy as np
import pandas as pd
import pytest

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
