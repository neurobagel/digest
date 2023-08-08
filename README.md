# Neuroimaging (proc)essing derivatives status (dash)board

`proc_dash` is a web dashboard that aims to provide interactive visualization and subject-level querying of raw and processed MRI data available for a neuroimaging dataset.

This tool ingests tabular processing derivative status files called `bagels`, which can be generated automatically by pipeline tracker scripts for datasets organized according to the standards of the [Nipoppy](https://github.com/neurodatascience/nipoppy) workflow.

Quickstart: https://dash.neurobagel.org/

## Preview
![alt text](https://github.com/neurobagel/proc_dash/blob/main/img/ui_overview_table.png?raw=true)

![alt text](https://github.com/neurobagel/proc_dash/blob/main/img/ui_overview_graphs.png?raw=true)


## Input schema
Input files to the dashboard contain long format data that must be formatted according to the [bagel schema](https://github.com/neurobagel/proc_dash/tree/main/schemas) (see also the schemas [README](https://github.com/neurobagel/proc_dash/tree/main/schemas#readme) for more info). A single file is expected to correspond to one dataset, but may contain status information for multiple processing pipelines for that dataset.

### Try it out
You can view and download a correctly formatted, minimal input tabular file [here](https://github.com/neurobagel/proc_dash/blob/main/tests/data/example_bagel.csv) to test out dashboard functionality.

## Steps to generate dashboard inputs (`bagel.csv`)
While the dashboard accepts any input CSV that is compliant with the [bagel schema](https://github.com/neurobagel/proc_dash/tree/main/schemas), the easiest way to obtain the necessary metadata from your dataset in a dashboard-ready file is to follow the [Nipoppy](https://neurobagel.org/nipoppy/overview/) structure for standardized organization of raw MRI data and processed outputs (data derivatives). `Nipoppy` provides scripts that can leverage this standardized dataset organization to automatically extract info about the raw imaging files and any processing pipelines that have been run on the data, and generate a dashboard-ready `bagel.csv` from the info.

Detailed instructions to get started using the `Nipoppy` workflow can be found in their [documentation](https://neurobagel.org/nipoppy/overview/). In brief, generating a `bagel.csv` for your dataset can be as simple as:
1. Installing `Nipoppy` to generate a dataset directory tree for your dataset (see [Installation](https://neurobagel.org/nipoppy/installation/) section of docs) that you can populate with your existing data
2. Update `Nipoppy` configuration to reflect the pipeline versions you are using (for tracking purposes), and augment your participant spreadsheet according to `Nipoppy` requirements (see [Configs](https://neurobagel.org/nipoppy/configs/) section of docs)
3. Run the tracker ([run_tracker.py](https://github.com/neurodatascience/nipoppy/blob/main/trackers/run_tracker.py)) for the relevant pipeline(s) for your dataset to generate a comprehensive `bagel.csv`
    - To see help text for this script: `python run_tracker.py --help`
    - This step can be repeated as needed to update the `bagel.csv` with newly processed subjects

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
`pytest` and `dash.testing` are used for testing dashboard functionality during development.

To run the tests, first install a WebDriver for the Dash app tests to interact with a Chrome browser, following the [ChromeDriver Getting Started Guide](https://chromedriver.chromium.org/getting-started). Once you have downloaded the correct ChromeDriver binary for your installed version of Chrome, add the location to your PATH by running the following command:
```bash
export PATH=$PATH:/path/to/your/folder/containing/ChromeDriver
```
You may have to repeat this step each time your Python environment is re-activated.

To run the tests, run the following command from the repository's root:
```bash
pytest tests
```
