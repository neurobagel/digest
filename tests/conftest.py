from pathlib import Path

import pytest
from selenium.webdriver.chrome.options import Options


def pytest_setup_options():
    """
    Ensure dash tests run in headless mode to run properly with GitHub actions.
    (Ref: https://community.plotly.com/t/dash-integration-testing-with-selenium-and-github-actions/43602)
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return options


@pytest.fixture(scope="session")
def bagels_path():
    return Path(__file__).absolute().parent / "data"
