import os

import pytest
from dash.testing.application_runners import import_app


@pytest.fixture(scope="function")
def test_server(dash_duo):
    app = import_app("proc_dash.app")
    dash_duo.start_server(app)

    yield dash_duo


@pytest.mark.parametrize(
    "valid_bagel,bagel_type,expected_element",
    [
        (
            "example_imaging_bagel.csv",
            "imaging",
            "#fig-pipeline-status-all-ses",
        ),
        ("example_pheno_bagel.csv", "phenotypic", "#advanced-filter-form"),
    ],
)
def test_001_upload_valid_bagel(
    test_server, bagels_path, valid_bagel, bagel_type, expected_element
):
    """
    Smoke test (e2e) for uploading a valid bagel input.
    Tests that an expected element for the uploaded data type is displayed after upload.
    """
    # Find element that contains input link. Utilize the web driver to get the element.
    upload = test_server.driver.find_element(
        "xpath",
        f"""//*[contains(@id,'"index":"{bagel_type}","type":"upload-data"')]/div/input""",
    )

    upload.send_keys(os.path.realpath(os.path.join(bagels_path, valid_bagel)))
    test_server.wait_for_style_to_equal(
        expected_element, "display", "block", timeout=4
    )

    assert "Error" not in test_server.find_element("#output-data-upload").text
    assert (
        test_server.get_logs() == []
    ), "browser console should contain no error"


def test_002_upload_invalid_imaging_bagel(test_server, bagels_path):
    """
    Given an invalid uploaded imaging bagel, displays an informative error message.
    NOTE: Different example files are iterated over instead of parameterized for efficiency,
    to reuse the same (function scoped) server instance.
    """
    invalid_input_output = {
        "example_missing-col_bagel.csv": "missing the following required imaging metadata columns: {'pipeline_starttime'}",
        "example_mismatch-subs_bagel.csv": "do not have the same number of subjects and sessions",
        "example_pheno_bagel.csv": "missing the following required imaging metadata columns",
    }

    upload = test_server.driver.find_element(
        "xpath",
        """//*[contains(@id,'"index":"imaging","type":"upload-data"')]/div/input""",
    )

    for invalid_bagel, err in invalid_input_output.items():
        upload.send_keys(
            os.path.realpath(os.path.join(bagels_path, invalid_bagel))
        )
        test_server.wait_for_contains_text(
            "#output-data-upload", err, timeout=4
        )
        assert err in test_server.find_element("#output-data-upload").text

    assert (
        test_server.get_logs() == []
    ), "browser console should contain no error"


def test_003_upload_invalid_phenotypic_bagel(test_server, bagels_path):
    """Given an invalid uploaded phenotypic bagel, displays an informative error message."""
    err = "missing the following required phenotypic metadata columns"
    upload = test_server.driver.find_element(
        "xpath",
        """//*[contains(@id,'"index":"phenotypic","type":"upload-data"')]/div/input""",
    )

    upload.send_keys(
        os.path.realpath(
            os.path.join(bagels_path, "example_imaging_bagel.csv")
        )
    )
    test_server.wait_for_contains_text("#output-data-upload", err, timeout=4)
    assert err in test_server.find_element("#output-data-upload").text

    assert (
        test_server.get_logs() == []
    ), "browser console should contain no error"
