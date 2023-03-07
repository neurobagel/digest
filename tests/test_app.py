import os

from dash.testing.application_runners import import_app
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))


def test_001_upload_valid_bagel(dash_duo, bagels_path):
    """Smoke test (e2e) for uploading a valid bagel input"""
    app = import_app("proc_dash.app")
    dash_duo.start_server(app)

    # Find element that contains input link. Utilize the web driver to get the element.
    element = dash_duo.driver.find_element(
        "xpath", '//*[@id="upload-data"]/div/input'
    )
    element.send_keys(os.path.join(bagels_path, "example_bagel.csv"))

    assert dash_duo.get_logs() == [], "browser console should contain no error"
