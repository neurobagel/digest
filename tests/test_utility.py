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
