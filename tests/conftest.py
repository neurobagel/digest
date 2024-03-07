from pathlib import Path

import chromedriver_autoinstaller
import pytest
from selenium.webdriver.chrome.options import Options


def pytest_setup_options():
    """
    Ensure dash tests run in headless mode to run properly with GitHub actions.
    (Ref: https://community.plotly.com/t/dash-integration-testing-with-selenium-and-github-actions/43602)
    """
    # Automatically install the chromedriver that matches the currently installed Chrome version on the system if it's not already installed
    # Mostly useful for running tests locally (to avoid having to update the chromedriver whenever there's a browser update),
    # as GitHub actions should already have a compatible chromedriver installed
    chromedriver_autoinstaller.install()

    options = Options()
    # See https://www.selenium.dev/blog/2023/headless-is-going-away/#after for the renewed headless mode. This is needed for the window rescaling to work properly.
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")

    # Set a large window size and (to be extra safe) rescale browser to ensure tested components are all visible and can be interacted with without scrolling
    options.add_argument("--window-size=1920x1080")
    options.add_argument("force-device-scale-factor=0.30")
    return options


@pytest.fixture(scope="session")
def bagels_path():
    return Path(__file__).absolute().parent / "data"
