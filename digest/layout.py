"""
Defines layout and layout components for dashboard.
"""

import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from . import utility as util

DEFAULT_DATASET_NAME = "Dataset"


def navbar():
    """Generates the dashboard navigation bar."""
    schemas = dbc.NavLink(
        children=[
            html.I(className="bi bi-box-arrow-up-right me-1"),
            "Input schema",
        ],
        href="https://github.com/neurobagel/proc_dash/tree/main/schemas",
        target="_blank",
    )

    github = dbc.NavLink(
        children=[
            html.I(className="bi bi-github me-1"),
            "GitHub",
        ],
        href="https://github.com/neurobagel/proc_dash",
        target="_blank",
    )

    navbar = dbc.Navbar(
        dbc.Container(
            [
                dbc.Row(
                    dbc.Col(
                        dbc.NavbarBrand(
                            "Neuroimaging Dataset Derivatives Status Dashboard"
                        )
                    ),
                    align="center",
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Nav(
                            [
                                schemas,
                                github,
                            ],
                        ),
                    ),
                    align="center",
                ),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
    )

    return navbar


def upload_buttons() -> list:
    """Returns list of upload components that is used to populate the upload container."""
    upload_imaging = dcc.Upload(
        id={"type": "upload-data", "index": "imaging", "btn_idx": 0},
        children=dbc.Button(
            "Drag & Drop or Select an Imaging CSV File",
            color="secondary",
        ),
        multiple=False,
    )

    upload_phenotypic = dcc.Upload(
        id={"type": "upload-data", "index": "phenotypic", "btn_idx": 1},
        children=dbc.Button(
            "Drag & Drop or Select a Phenotypic CSV File",
            color="secondary",
        ),
        multiple=False,
    )

    return [upload_imaging, upload_phenotypic]


def upload_container():
    return html.Div(
        id="upload-buttons",
        children=upload_buttons(),
        className="hstack gap-3",
    )


def sample_data_button():
    """Generates the button to view sample input files."""
    return dbc.Button(
        "Example input files",
        color="light",
        href="https://github.com/neurobagel/proc_dash/blob/main/example_bagels",
        target="_blank",  # open external site in new tab
    )


def dataset_name_dialog():
    """Generates the modal dialog for entering the dataset name."""
    return dbc.Modal(
        children=[
            dbc.ModalHeader(
                dbc.ModalTitle("Enter the dataset name:"), close_button=False
            ),
            dbc.ModalBody(
                dbc.Input(
                    id="dataset-name-input",
                    placeholder=DEFAULT_DATASET_NAME,
                    type="text",
                )
            ),
            dbc.ModalFooter(
                [
                    dcc.Markdown("*Tip: To skip, press Submit or ESC*"),
                    dbc.Button(
                        "Submit",
                        id="submit-name",
                        className="ms-auto",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id="dataset-name-modal",
        is_open=False,
        backdrop="static",  # do not close dialog when user clicks elsewhere on screen
    )


def dataset_summary_card():
    """Generates the card that displays the dataset summary."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(
                    children=DEFAULT_DATASET_NAME,
                    id="summary-title",
                    className="card-title",
                ),
                html.P(
                    id="dataset-summary",
                    style={"whiteSpace": "pre"},  # preserve newlines
                    className="card-text",
                ),
            ],
        ),
        id="dataset-summary-card",
        style={"display": "none"},
    )


def table_summary():
    """Generates text elements that display summary info about an active datatable."""
    return html.Div(
        children=[
            html.Div(
                # TODO: Merge this component with the input-filename component once error alert elements are implemented
                id="upload-message",
                children="Upload a CSV file to begin.",
            ),
            html.Div(
                id="column-count",
            ),
            html.Div(
                id="matching-participants",
                style={"margin-left": "15px"},
            ),
            html.Div(
                id="matching-records",
                style={"margin-left": "15px"},
            ),
        ],
        style={"display": "inline-flex"},
    )


def status_legend_card():
    """Generates the card that displays the legend for processing pipeline statuses."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(
                    "Processing status legend",
                    className="card-title",
                ),
                html.P(
                    children=util.construct_legend_str(
                        util.PIPE_COMPLETE_STATUS_SHORT_DESC
                    ),
                    style={"whiteSpace": "pre"},  # preserve newlines
                    className="card-text",
                ),
            ]
        ),
        id="processing-status-legend",
        style={"display": "none"},
    )


def overview_table():
    """Generates overview table for the tasks in the tabular data (imaging or phenotypic)."""
    return dash_table.DataTable(
        id="interactive-datatable",
        data=None,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        page_size=50,
        # fixed_rows={"headers": True},
        style_table={"height": "400px", "overflowY": "auto"},
        # TODO: When table is large, having both vertical + horizontal scrollbars doesn't look great.
        # Consider removing fixed height and using only page_size + setting overflowX to allow horizontal scroll.
        # Or, use relative css units here, e.g. vh for fractions of the viewport-height: https://www.w3schools.com/cssref/css_units.php
        # Also, should fix participant_id column, as long as it's first in the dataframe.
        style_cell={
            "fontSize": 13  # accounts for font size inflation by dbc theme
        },
        style_header={
            "position": "sticky",
            "top": 0,
        },  # Workaround to fixed_rows that does not impact column width. Could also specify widths in style_cell
        export_format="none",
    )


def advanced_filter_form_title():
    """Generates the title and tooltip for the advanced filtering form."""
    return html.Div(
        [
            html.H5(
                children="Advanced filtering options",
            ),
            html.I(
                className="bi bi-question-circle ms-1",
                id="tooltip-question-target",
            ),
            dbc.Tooltip(
                dcc.Markdown(
                    "Filter based on multiple sessions simultaneously. "
                    "Note that any data filters selected here will always be applied *before* any column filters specified directly in the data table."
                ),
                target="tooltip-question-target",
            ),
        ],
        style={"display": "inline-flex"},
    )


def session_filter_form():
    """Generates the form for advanced session filtering."""
    session_options = html.Div(
        [
            dbc.Label(
                "Filter by session(s):",
                html_for="session-dropdown",
                className="mb-0",
            ),
            dcc.Dropdown(
                id="session-dropdown",
                options=[],
                multi=True,
                placeholder="Select one or more sessions...",
            ),
        ],
        className="mb-2",  # Add margin to keep dropdowns spaced apart
    )

    selection_operator = html.Div(
        [
            dbc.Label(
                "Session selection operator:",
                html_for="select-operator",
                className="mb-0",
            ),
            dcc.RadioItems(
                id="select-operator",
                options=[
                    {
                        "label": html.Span("AND", id="and-selector"),
                        "value": "AND",
                    },
                    {
                        "label": html.Span("OR", id="or-selector"),
                        "value": "OR",
                    },
                ],
                value="AND",
                inline=True,
                inputClassName="me-1",
                labelClassName="me-3",
            ),
            dbc.Tooltip(
                "All selected sessions are present for the subject and (for imaging data only) match the pipeline status filters.",
                target="and-selector",
            ),
            dbc.Tooltip(
                "Any selected session is present for the subject and (for imaging data only) matches the pipeline status filters.",
                target="or-selector",
            ),
        ],
        className="mb-2",
    )

    return dbc.Form(
        [
            session_options,
            selection_operator,
        ],
    )


def phenotypic_plotting_form():
    """Generates the dropdown for selecting a phenotypic column to plot."""
    return html.Div(
        [
            html.H5(children="Visualize column data"),
            dbc.Label(
                "Select a column to plot:",
                html_for="phenotypic-column-plotting-dropdown",
                className="mb-0",
            ),
            dcc.Dropdown(
                id="phenotypic-column-plotting-dropdown",
                options=[],
            ),
        ],
        id="phenotypic-plotting-form",
        style={"display": "none"},
    )


def column_summary_card():
    """Generates the card that displays summary statistics about a selected phenotypic column."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(
                    id="column-summary-title",
                    className="card-title",
                ),
                html.P(
                    id="column-summary",
                    style={"whiteSpace": "pre-wrap"},  # preserve newlines
                    className="card-text",
                ),
            ],
        ),
        id="column-summary-card",
        style={"display": "none"},
    )


def session_toggle_switch():
    """Generates a switch that toggles whether the column plot is stratified by session."""
    return dbc.Switch(
        id="session-toggle-switch",
        label="Stratify plot by session",
        value=False,
        style={"display": "none"},
    )


def construct_layout():
    """Generates the overall dashboard layout."""
    return html.Div(
        children=[
            navbar(),
            dcc.Store(id="memory-filename"),
            dcc.Store(id="memory-sessions"),
            dcc.Store(id="memory-overview"),
            dcc.Store(id="memory-pipelines"),
            html.Div(
                children=[upload_container(), sample_data_button()],
                style={"margin-top": "10px", "margin-bottom": "10px"},
                className="hstack gap-3",
            ),
            dataset_name_dialog(),
            html.Div(
                id="output-data-upload",
                children=[
                    html.H4(id="input-filename"),
                    dbc.Row(
                        [
                            dbc.Col(
                                table_summary(),
                                align="end",
                            ),
                            dbc.Col(
                                dataset_summary_card(),
                            ),
                        ]
                    ),
                    overview_table(),
                ],
                style={"margin-top": "10px", "margin-bottom": "10px"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(advanced_filter_form_title()),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        session_filter_form(),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.Row(
                                            id="pipeline-dropdown-container",
                                            children=[],
                                        ),
                                    ),
                                ]
                            ),
                        ],
                        id="advanced-filter-form",
                        style={"display": "none"},
                    ),
                    dbc.Col(
                        phenotypic_plotting_form(),
                        width=3,
                    ),
                ]
            ),
            status_legend_card(),
            dbc.Row(
                [
                    # NOTE: Legend displayed for both graphs so that user can toggle visibility of status data
                    dbc.Col(
                        dcc.Graph(
                            id="fig-pipeline-status", style={"display": "none"}
                        )
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id="fig-pipeline-status-all-ses",
                            style={"display": "none"},
                        )
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id="fig-column-histogram",
                            style={"display": "none"},
                        ),
                        width=8,
                    ),
                    dbc.Col(
                        dbc.Stack(
                            [
                                column_summary_card(),
                                session_toggle_switch(),
                            ],
                            gap=3,
                        ),
                    ),
                ],
                align="center",
            ),
        ],
        style={"padding": "10px 10px 10px 10px"},
    )
