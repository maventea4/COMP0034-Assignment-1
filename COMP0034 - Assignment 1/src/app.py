import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go

# Initialize the app
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Required for deployment

# Load crime data
def load_crime_data():
    try:
        crime_csv = Path(__file__).parent.parent.joinpath('data', 'crime_cleaned.csv')
        crime_df = pd.read_csv(crime_csv)
        return crime_df
    except FileNotFoundError:
        print("Crime data file not found.")
        return None
    except pd.errors.EmptyDataError:
        print("Crime data file is empty.")
        return None

# Load London boroughs GeoJSON -- Source: https://plotly.com/python/tile-county-choropleth/
def load_geojson():
    try:
        geojson_path = Path(__file__).parent.parent.joinpath('Data', 'london-boroughs_1179.geojson')
        # Data source: https://cartographyvectors.com/map/1179-london-boroughs
        with open(geojson_path, 'r') as file:
            geojson_data = json.load(file)
        return geojson_data
    except FileNotFoundError:
        print("GeoJSON file not found.")
        return None

crime_df = load_crime_data()
geojson_data = load_geojson()

# Melt the data for visualization
def melt_crime_data(df):
    if df is not None:
        return df.melt(id_vars=['BoroughName', 'MajorText', 'MinorText'], 
                       var_name='Month', 
                       value_name='CrimeCount')
    return df

# Function to return an empty figure with a message if errors are caught
def empty_figure(message="No data available"):
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
                "font": {"size": 20}
            }
        ]
    )
    return fig

crime_df = melt_crime_data(crime_df)

# Extract unique boroughs
borough_options = [{'label': b, 'value': b} for b in crime_df['BoroughName'].unique()] if crime_df is not None else [{'label': 'No data available', 'value': ''}]

# Define the app layout
app.layout = html.Div([
    dbc.Container([
        html.H1("SafeCity", className="display-2 text-center mt-5", style={"color": "#ffffff", "font-weight": "bold"}),
        html.P("A safer London for all!", className="lead text-center", style={"color": "#b0c4de", "font-size": "1.3rem", "font-style": "italic", "font-weight": "bold"}),

        # Crime heatmap
        html.P("Frequency of Crime by Borough", style={"color": "#b0c4de", "font-size": "1.0rem"}),
        dcc.Graph(id='crime-heatmap'),

        # Dropdown for borough selection
        dcc.Dropdown(
            id='borough-selection',
            options=borough_options,
            placeholder="Select a Borough...",
            className="mt-4",
            persistence=True,
            persistence_type='session',
            clearable=True
        ),

        # Button to show graphs
        html.Button("Go to Dashboard", id="navigate-button", className="btn btn-primary mt-3", n_clicks=0),

        # Graph containers
        html.Div([
            dcc.Graph(id='crime-trend-graph'),
            html.P("*The graph is interactive. You can zoom in using the lasso tool or crop feature.",
                   style={"color": "#d3d3d3", "font-size": "0.8rem"}),

            dcc.Graph(id='major-crime-pie-chart', style={'display': 'none'}),
            html.P("*The pie chart is interactive. Click on the legend to remove a crime type.",
                   style={"color": "#d3d3d3", "font-size": "0.8rem"}),

            html.P("Below, the time series shows the evolution of each major crime type, segmented further where applicable.",
                   style={"color": "#b0c4de", "font-size": "1.0rem"}),
            dcc.Dropdown(
                id='major-crime-selection',
                options=[],  
                placeholder="Select a Major Crime Type...",
                style={'display': 'none'},
                className="mt-4"
            ),
            
            dcc.Graph(id='crime-breakdown-graph'),
            html.P("*The graph is interactive. You can zoom in using the lasso tool or crop feature.",
                   style={"color": "#d3d3d3", "font-size": "0.8rem"}),

        ], id="graph-container", style={'display': 'none'})
    ], style={"max-width": "960px"}),  
], style={"background-color": "#0a1f44", "padding": "40px 0"})


# Callback for heatmap generation
@app.callback(
    Output('crime-heatmap', 'figure'),
    [Input('navigate-button', 'n_clicks')]
)
def update_heatmap(n_clicks):
    if crime_df is None or geojson_data is None:
        return empty_figure("Error: No data available")

    crime_summary = crime_df.groupby('BoroughName')['CrimeCount'].sum().reset_index()
    
    heatmap_fig = px.choropleth_map(
        crime_summary,
        geojson=geojson_data,
        locations='BoroughName',
        featureidkey="properties.name",
        color='CrimeCount',
        color_continuous_scale="Reds",
        center={"lat": 51.5074, "lon": -0.1278},
        zoom=9,
        title="Crime Heatmap of London"
    )
    heatmap_fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        mapbox_style="carto-positron"
    )
    return heatmap_fig

# Combined callback to handle major crime type dropdown visibility and update graphs
@app.callback(
    [Output('graph-container', 'style'),
     Output('crime-trend-graph', 'figure'),
     Output('major-crime-pie-chart', 'figure'),
     Output('major-crime-pie-chart', 'style'),
     Output('crime-breakdown-graph', 'figure'),
     Output('major-crime-selection', 'options'),
     Output('major-crime-selection', 'style'),
     Output('major-crime-selection', 'value')],
    [Input('navigate-button', 'n_clicks'),
     Input('major-crime-selection', 'value')],
    [State('borough-selection', 'value')]
)
def update_graphs_and_dropdown(n_clicks, selected_major_crime, selected_borough):
    if n_clicks == 0 or crime_df is None or not selected_borough:
        return {'display': 'none'}, dash.no_update, dash.no_update, {'display': 'none'}, dash.no_update, [], {'display': 'none'}, dash.no_update
    
    # Filter dataset
    filtered_df = crime_df[crime_df['BoroughName'] == selected_borough]

    # First Graph: Overall Crime Trend Over Time
    trend_fig = px.line(
        filtered_df.groupby('Month').sum().reset_index(), x='Month', y='CrimeCount',
        title=f'Overall Crime Trend in {selected_borough} Over Time',
        labels={'CrimeCount': 'Crime Count', 'Month': 'Month'},
        line_shape="linear"
    )
    trend_fig.update_layout(
        plot_bgcolor="#f8f9fa", 
        paper_bgcolor="#f8f9fa",
        xaxis=dict(showgrid=True, tickangle=-45),  
        yaxis=dict(showgrid=True), 
        font=dict(family="Arial, sans-serif")
    )

    # Second Graph: Pie Chart for Count of Each Major Crime Type
    pie_chart_df = filtered_df.groupby('MajorText').sum().reset_index()
    pie_chart_fig = px.pie(
        pie_chart_df, names='MajorText', values='CrimeCount',
        title=f'Count of Each Major Crime Type in {selected_borough}',
        labels={'CrimeCount': 'Crime Count', 'MajorText': 'Major Crime Type'}
    )
    pie_chart_fig.update_layout(
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
        font=dict(family="Arial, sans-serif")
    )

    # Third Graph: Crime Breakdown by Selected Major Crime Type
    if selected_major_crime:
        breakdown_df = filtered_df[filtered_df['MajorText'] == selected_major_crime]
        breakdown_fig = px.line(
            breakdown_df, x='Month', y='CrimeCount', color='MinorText',
            title=f'Crime Trend Over Time for {selected_major_crime} in {selected_borough}',
            labels={'CrimeCount': 'Crime Count', 'Month': 'Month'},
            line_shape="linear"
        )
        breakdown_fig.update_layout(
            plot_bgcolor="#f8f9fa",
            paper_bgcolor="#f8f9fa",
            xaxis=dict(showgrid=True, tickangle=-45),
            yaxis=dict(showgrid=True),
            font=dict(family="Arial, sans-serif")
        )
    else:
        breakdown_fig = px.line()

    # Show major crime type dropdown
    major_crime_options = [{'label': mc, 'value': mc} for mc in filtered_df['MajorText'].unique()]
    major_crime_dropdown_style = {'display': 'block'}

    return {'display': 'block'}, trend_fig, pie_chart_fig, {'display': 'block'}, breakdown_fig, major_crime_options, major_crime_dropdown_style, None

if __name__ == '__main__':
    app.run_server(debug=True)