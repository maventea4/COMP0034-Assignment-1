import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go

# Initialise the app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server 


# Load crime data
def load_crime_data():
    """Loads and processes the crime data from a CSV file.

    Attempts to load crime data from a predefined path and renames columns.

    Returns:
        DataFrame or None: Processed crime data or None if there was an error.
    """

    try:
        crime_csv = Path(__file__).parent.parent.joinpath("data", "crime_cleaned.csv")
        crime_df = pd.read_csv(crime_csv)
        # Rename columns to match the new naming convention
        crime_df.rename(
            columns={
                "MajorText": "MajorCrimeCategory",
                "MinorText": "CrimeSubcategory",
            },
            inplace=True,
        )
        return crime_df
    except FileNotFoundError:
        print("Crime data file not found.")
        return None
    except pd.errors.EmptyDataError:
        print("Crime data file is empty.")
        return None


# Load London boroughs GeoJSON -- Source: https://plotly.com/python/tile-county-choropleth/
def load_geojson():
    """Loads the London boroughs GeoJSON data from a predetermined file path.

    Returns:
        dict or None: Loaded GeoJSON data or None if there was an error.
    """
    try:
        geojson_path = Path(__file__).parent.parent.joinpath(
            "Data", "london-boroughs_1179.geojson"
        )
        # Data source: https://cartographyvectors.com/map/1179-london-boroughs
        with open(geojson_path, "r") as file:
            geojson_data = json.load(file)
        return geojson_data
    except FileNotFoundError:
        print("GeoJSON file not found.")
        return None


crime_df = load_crime_data()
geojson_data = load_geojson()


# Melt the data for visualisation
def melt_crime_data(df):
    """Converts the crime data DataFrame into a long format for easier visualisation.

    Args:
        df (DataFrame): Crime data DataFrame.

    Returns:
        DataFrame: Long format DataFrame or None if input is invalid.
    """

    if df is not None:
        return df.melt(
            id_vars=["BoroughName", "MajorCrimeCategory", "CrimeSubcategory"],
            var_name="Month",
            value_name="CrimeCount",
        )
    return df


# Function to return an empty figure with a message if errors are caught
def empty_figure(message="No data available"):
    """Generates an empty Plotly figure with the specified error message.

    Args:
        message (str): Message to display on the figure.

    Returns:
        plotly.graph_objects.Figure: Empty figure with a message.
    """
    fig = go.Figure()
    fig.update_layout(
        title=message,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 20},
            }
        ],
    )
    return fig

crime_df = melt_crime_data(crime_df)

def get_borough_options(df):
    """Generates a list of borough options for the dropdown.

    Args:
        df (DataFrame): The crime data DataFrame.

    Returns:
        list: A list of dictionaries for the borough dropdown options.
    """
    if df is not None:
        return [
            {"label": borough, "value": borough}
            for borough in df["BoroughName"].unique()
        ]
    return [{"label": "No data available", "value": ""}]

borough_options = get_borough_options(crime_df)

# Define the app layout
app.layout = html.Div(
    [
        dbc.Container(
            [
                html.H1(
                    "SafeCity",
                    className="display-2 text-center mt-5",
                    style={"color": "#ffffff", "font-weight": "bold"},
                ),
                html.P(
                    "A safer London for all!",
                    className="lead text-center",
                    style={
                        "color": "#b0c4de",
                        "font-size": "1.3rem",
                        "font-style": "italic",
                        "font-weight": "bold",
                    },
                ),
                # Crime heatmap
                html.P(
                    "Frequency of Crime by Borough",
                    style={"color": "#b0c4de", "font-size": "1.0rem"},
                ),
                dcc.Graph(id="crime-heatmap"),
                # Dropdown for borough selection
                dcc.Dropdown(
                    id="borough-selection",
                    options=borough_options,
                    placeholder="Select a Borough...",
                    className="mt-4",
                    persistence=True,
                    persistence_type="session",
                    clearable=True,
                ),
                # Button to show graphs
                html.Button(
                    "Go to Dashboard",
                    id="navigate-button",
                    className="btn btn-primary mt-3",
                    n_clicks=0,
                ),
                # Graph containers
                html.Div(
                    [
                        dcc.Graph(id="crime-trend-graph"),
                        html.P(
                            "*The graph is interactive. You can zoom in on specific dates using the lasso tool or crop feature.",
                            style={"color": "#d3d3d3", "font-size": "0.8rem"},
                        ),
                        dcc.Graph(
                            id="major-crime-pie-chart", style={"display": "none"}
                        ),
                        html.P(
                            "*The pie chart is interactive. Click on the legend to remove a crime type.",
                            style={"color": "#d3d3d3", "font-size": "0.8rem"},
                        ),
                        html.P(
                            "Below, the time series shows the evolution of each major crime type, segmented further where applicable.",
                            style={"color": "#b0c4de", "font-size": "1.0rem"},
                        ),
                        dcc.Dropdown(
                            id="major-crime-selection",
                            options=[],
                            placeholder="Select a Major Crime Type...",
                            style={"display": "none"},
                            className="mt-4",
                        ),
                        dcc.Graph(id="crime-breakdown-graph"),
                        html.P(
                            "*The graph is interactive. You can zoom in on specific dates using the lasso tool or crop feature.",
                            style={"color": "#d3d3d3", "font-size": "0.8rem"},
                        ),
                    ],
                    id="graph-container",
                    style={"display": "none"},
                ),
                html.Div(
                    [
                        html.P(
                            "Data sourced from the Metropolitan Police Service under the UK Open Government License (OGL v2).",
                            style={
                                "color": "#b0c4de",
                                "text-align": "center",
                                "margin-top": "10px",
                            },
                        )
                    ],
                    className="mt-5",
                ),
            ],
            style={"max-width": "960px"},
        ),
    ],
    style={"background-color": "#0a1f44", "padding": "40px 0"},
)


# Callback for heatmap generation
@app.callback(Output("crime-heatmap", "figure"), [Input("navigate-button", "n_clicks")])
def update_heatmap(n_clicks):
    """Updates the crime heatmap based on user input.

    Args:
        n_clicks (int): Number of times the 'Go to Dashboard' button has been clicked.

    Returns:
        plotly.graph_objects.Figure: Updated heatmap figure.
    """
    if crime_df is None or geojson_data is None:
        return empty_figure("Error: No data available")

    crime_summary = crime_df.groupby("BoroughName")["CrimeCount"].sum().reset_index()

    heatmap_fig = px.choropleth_map(
        crime_summary,
        geojson=geojson_data,
        locations="BoroughName",
        featureidkey="properties.name",
        color="CrimeCount",
        color_continuous_scale="Reds",
        center={"lat": 51.5074, "lon": -0.1278},
        zoom=9,
        title="Crime Heatmap of London",
    )
    heatmap_fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0}, mapbox_style="carto-positron"
    )
    return heatmap_fig


# Combined callback to handle major crime type dropdown visibility and update graphs
@app.callback(
    [
        Output("graph-container", "style"),
        Output("crime-trend-graph", "figure"),
        Output("major-crime-pie-chart", "figure"),
        Output("major-crime-pie-chart", "style"),
        Output("crime-breakdown-graph", "figure"),
        Output("major-crime-selection", "options"),
        Output("major-crime-selection", "style"),
        Output("major-crime-selection", "value"),
    ],
    [Input("navigate-button", "n_clicks"), Input("major-crime-selection", "value")],
    [State("borough-selection", "value")],
)
def update_graphs_and_dropdown(n_clicks, selected_major_crime, selected_borough):
    """Updates graphs and dropdown based on user input.

    Args:
        n_clicks (int): Number of times the 'Go to Dashboard' button was clicked.
        selected_major_crime (str): Selected major crime type.
        selected_borough (str): Selected borough.

    Returns:
        tuple: Graph container style, updated crime trend graph, pie chart, crime breakdown graph,
               major crime dropdown options, dropdown style, and selected major crime value.
    """

    if n_clicks == 0 or crime_df is None or not selected_borough:
        return (
            {"display": "none"},
            dash.no_update,
            dash.no_update,
            {"display": "none"},
            dash.no_update,
            [],
            {"display": "none"},
            dash.no_update,
        )

    # Filter dataset
    filtered_df = crime_df[crime_df["BoroughName"] == selected_borough]

    # First Graph: Overall Crime Trend Over Time
    trend_fig = px.line(
        filtered_df.groupby("Month").sum().reset_index(),
        x="Month",
        y="CrimeCount",
        title=f"Overall Crime Trend in {selected_borough} Over Time",
        labels={"CrimeCount": "Crime Count", "Month": "Month"},
        line_shape="linear",
    )
    trend_fig.update_layout(
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
        xaxis=dict(showgrid=True, tickangle=-45),
        yaxis=dict(showgrid=True),
        font=dict(family="Arial, sans-serif"),
    )

    # Second Graph: Pie Chart for Count of Each Major Crime Type
    pie_chart_df = filtered_df.groupby("MajorCrimeCategory").sum().reset_index()
    pie_chart_fig = px.pie(
        pie_chart_df,
        names="MajorCrimeCategory",
        values="CrimeCount",
        title=f"Count of Each Major Crime Type in {selected_borough}",
        labels={"CrimeCount": "Crime Count", "MajorCrimeCategory": "Major Crime Type"},
    )
    pie_chart_fig.update_layout(
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
        font=dict(family="Arial, sans-serif"),
    )

    # Third Graph: Crime Breakdown by Selected Major Crime Type
    if selected_major_crime:
        breakdown_df = filtered_df[
            filtered_df["MajorCrimeCategory"] == selected_major_crime
        ]
        breakdown_fig = px.line(
            breakdown_df,
            x="Month",
            y="CrimeCount",
            color="CrimeSubcategory",
            title=f"Crime Trend Over Time for {selected_major_crime} in {selected_borough}",
            labels={"CrimeCount": "Crime Count", "Month": "Month"},
            line_shape="linear",
        )
        breakdown_fig.update_layout(
            plot_bgcolor="#f8f9fa",
            paper_bgcolor="#f8f9fa",
            xaxis=dict(showgrid=True, tickangle=-45),
            yaxis=dict(showgrid=True),
            font=dict(family="Arial, sans-serif"),
        )
    else:
        breakdown_fig = px.line()

    # Show major crime type dropdown
    major_crime_options = [
        {"label": mc, "value": mc} for mc in filtered_df["MajorCrimeCategory"].unique()
    ]
    major_crime_dropdown_style = {"display": "block"}

    return (
        {"display": "block"},
        trend_fig,
        pie_chart_fig,
        {"display": "block"},
        breakdown_fig,
        major_crime_options,
        major_crime_dropdown_style,
        None,
    )


if __name__ == "__main__":
    app.run_server(debug=True)
