# Neurobagel participant derivatives status dashboard

A web dashboard providing interactive visualization of statuses of processing tasks performed on a neuroimaging dataset.

This tool ingests processing pipeline output validation .csv files generated as part of the [mr_proc](https://github.com/neurodatascience/mr_proc) workflow.

## Local development
To install `dash` from the source repository, run the following in a Python environment:
```bash
git clone https://github.com/neurobagel/dash.git
cd dash
pip install -r requirements.txt
```

To launch the app locally:
```bash
python -m proc-dash.app
```
Once the server is running, the dashboard can be accessed at http://127.0.0.1:8050/ in your browser.
