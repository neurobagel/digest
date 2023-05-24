# Neuroimaging (proc)essing derivatives status (dash)board

`proc_dash` is a web dashboard providing interactive visualization of statuses of processing tasks performed on a neuroimaging dataset.

This tool ingests tabular processing derivative status files called `bagels`, which can be generated automatically by pipeline tracker scripts for datasets organized according to the standards of the [mr_proc](https://github.com/neurodatascience/mr_proc) workflow.

## Preview
![alt text](https://github.com/neurobagel/proc_dash/blob/main/img/ui_overview_table.png?raw=true)

![alt text](https://github.com/neurobagel/proc_dash/blob/main/img/ui_overview_graphs.png?raw=true)


## Input schema
Input files to the dashboard contain long format data that must be formatted according to the [bagel schema](https://github.com/neurobagel/proc_dash/tree/main/schemas). A single file is expected to correspond to one dataset, but may contain status information for multiple processing pipelines for that dataset.

### Try it out
You can view and download a correctly formatted, minimal input tabular file [here](https://github.com/neurobagel/proc_dash/blob/main/tests/data/example_bagel.csv) to test out dashboard functionality.

## Local development
To install `dash` from the source repository, run the following in a Python environment:
```bash
git clone https://github.com/neurobagel/proc_dash.git
cd dash
pip install -r requirements.txt
```

To launch the app locally:
```bash
python -m proc_dash.app
```
Once the server is running, the dashboard can be accessed at http://127.0.0.1:8050/ in your browser.

### Testing
`pytest` and `dash.testing` are used for testing dashboard functionality.

To run the tests, first install a WebDriver for the Dash app tests to interact with a Chrome browser, following the [ChromeDriver Getting Started Guide](https://chromedriver.chromium.org/getting-started). Once you have downloaded the correct ChromeDriver binary for your installed version of Chrome, add the location to your PATH by running the following command:
```bash
export PATH=$PATH:/path/to/your/folder/containing/ChromeDriver
```
You may have to repeat this step each time your Python environment is re-activated.

To run the tests, run the following command from the repository's root:
```bash
pytest tests
```
