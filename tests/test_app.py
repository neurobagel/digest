import os

import pytest
from dash.testing.application_runners import import_app


@pytest.fixture(scope="function")
def test_server(dash_duo):
    app = import_app("proc_dash.app")
    dash_duo.start_server(app)

    yield dash_duo


def test_001_upload_valid_bagel(test_server, bagels_path):
    """Smoke test (e2e) for uploading a valid bagel input"""
    # app = import_app("proc_dash.app")
    # dash_duo.start_server(app)

    # Find element that contains input link. Utilize the web driver to get the element.
    element = test_server.driver.find_element(
        "xpath", '//*[@id="upload-data"]/div/input'
    )
    element.send_keys(os.path.join(bagels_path, "example_bagel.csv"))
    test_server.wait_for_element("#output-data-upload", timeout=4)

    assert (
        test_server.get_logs() == []
    ), "browser console should contain no error"


def test_002_upload_invalid_bagel(test_server, bagels_path):
    """
    Given invalid uploaded bagel.csv, displays an informative error message.
    NOTE: Different example files are iterated over instead of parameterized for efficiency,
    to reuse the same (function scoped) server instance.
    """
    invalid_input_output = {
        "example_missing-col_bagel.csv": "missing the following required metadata columns: {'pipeline_starttime'}",
        "example_mismatch-subs_bagel.csv": "do not have the same number of subjects and sessions",
    }

    element = test_server.driver.find_element(
        "xpath", '//*[@id="upload-data"]/div/input'
    )

    for invalid_bagel, err in invalid_input_output.items():
        element.send_keys(os.path.join(bagels_path, invalid_bagel))
        test_server.wait_for_contains_text(
            "#output-data-upload", err, timeout=4
        )
        assert err in test_server.find_element("#output-data-upload").text

    assert (
        test_server.get_logs() == []
    ), "browser console should contain no error"
