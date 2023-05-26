from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import environ
import dash_bootstrap_components as dbc
import numpy as np
from app6 import generate_3d_scatter
import requests
import dash

# ENV setup
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env()

# Database Connection with our ENV Variables
conn = psycopg2.connect(
    host=env('DATABASE_HOST'),
    database=env('DATABASE_NAME'),
    user=env('DATABASE_USER'),
    password=env('DATABASE_PASSWORD'),
)

# How we search through the database after connection
cursor = conn.cursor()
cursor.execute('SELECT * FROM "public"."job_data_job"')
rows = cursor.fetchall()
cursor.close()
conn.close()

# Extract the data from the fetched rows
data = {
    "title": [],
    "Latitude": [],
    "Longitude": [],
    "Value": [],
    "industry": [],
    "job_function": [],
    "employment_type": [],
    "education": [],
    "salary_high": [],
    "skills":[],
}


for row in rows:
    data["employment_type"].append(row[1])
    data["industry"].append(row[2])
    data["education"].append(row[6])
    data["title"].append(row[10])  # Assuming the x-values are in the first column
    data["Latitude"].append(row[11])
    data["Longitude"].append(row[12])
    data["skills"].append(row[13])
    if row[8] is None:
        data["Value"].append(100000)
    else:
        data["Value"].append(row[8]) # Salary
    if row[8] is None:
        data["salary_high"].append(100000)
    else:
        data["salary_high"].append(row[8])


# Determine the maximum length of the lists in the data dictionary
max_length = max(len(v) for v in data.values())

# Fill the lists with NaN values to make them the same length
for key in data:
    diff = max_length - len(data[key])
    if diff > 0:
        data[key].extend([np.nan] * diff)

df = pd.DataFrame(data, columns=['id', 'employment_type', 'industry', 'job_function', 'senority', 'location', 'education', 'months_experience', 'salary_high', 'salary_low', 'title', 'lat', 'lon', 'skills'])

# api data for cost of living entry
url = f"https://tech-relocator-backend.vercel.app/api/v1/col/?state"

response = requests.get(url)
api_data = response.json()

api_data = [
    {
        "id": entry["id"],
        "rank": entry["rank"],
        "state": entry["state"],
        "index": entry["index"],
        "grocery": entry["grocery"],
        "housing": entry["housing"],
        "utilities": entry["utilities"],
        "transportation": entry["transportation"],
        "health": entry["health"],
        "misc": entry["misc"]
    }
    for entry in api_data
]

# Start app and call in the theme
app = Dash(__name__, external_stylesheets=[dbc.themes.VAPOR])
server = app.server



# Creates the layout for all divs in our app, each div contains an object
app.layout = dbc.Container([
    dbc.NavbarSimple(
        # children=[
        #     dbc.NavItem(dbc.NavLink("Home", href="#")),
        #     dbc.NavItem(dbc.NavLink("About", href="#")),
        #     dbc.NavItem(dbc.NavLink("Contact", href="#")),
        #     ],
        brand="Tech Relocator",
        brand_href="#",
        color="primary",
        dark=True,
    ),
    dbc.Container(
        [
            html.H1("Cost of Living Per State"),
            dbc.Input(
                id="state-input",
                type="text",
                placeholder="Enter state(s) separated by commas",
            ),
            html.Br(),
            dbc.Row(
                dbc.Col(
                    id="table-container",
                    children=[],
                    width={"size": 8, "offset": 2},
                ),
            ),
        ],
        className="mt-4",
    ),
    dbc.Row(
        children=[
            html.H1("Tech Jobs Across the US"),
            html.Button("Update Position", id="update_btn"),
            dcc.Graph(
                id='map-graph',
                figure=go.Figure(

                    data=[
                        go.Scattermapbox(
                            lat=data['Latitude'],
                            lon=data['Longitude'],
                            mode='markers',
                            marker=go.scattermapbox.Marker(
                                size=10,
                                color=data['Value'],
                                colorscale='portland',
                                colorbar=dict(title='Salary')
                            ),
                            text=data['title']
                        )
                    ],
                    layout=go.Layout(
                        mapbox=dict(
                            style='mapbox://styles/mapbox/dark-v10',
                            accesstoken=env('MAPBOX'),
                            center=dict(lat=39, lon=-98),
                            zoom=3,
                        ),
                        autosize=True
                    )
                ).update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(
                        l=0,
                        r=0,
                        b=0,
                        t=0,
                        pad=0,
                    )
                )
            ),
            dcc.Geolocation(id="geolocation"),
            html.Div(id="text_position"),
        ]
    ),
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    html.H1("Employment Type"),
                    dcc.Graph(id='employment-pie-chart'),
                    html.H1("Industry vs Experience Required vs Location"),
                    generate_3d_scatter()]
            )]
    ),
])




@app.callback(Output("geolocation", "update_now"), Input("update_btn", "n_clicks"))
def update_now(click):
    return True if click and click > 0 else False


@app.callback(
    Output("text_position", "children"),
    Output('map-graph', 'figure'),
    Input("geolocation", "local_date"),
    Input("geolocation", "position"),
)
def display_output(date, pos):
    if pos is None:
        pos = {'lat': 47.6034, 'lon': -122.3414, 'accuracy': 1, 'alt': None, 'alt_accuracy': None, 'speed': None,
         'heading': None}
        location_string = "Using generic location of Seattle, WA"
    else:
        location_string = f"As of {date} your location was: lat {pos['lat']}, lon {pos['lon']}, accuracy {pos['accuracy']} meters"

    if pos:
        lat = pos['lat']
        lon = pos['lon']
        center = dict(lat=lat, lon=lon)

        figure = go.Figure(
            data=[
                go.Scattermapbox(
                    lat=data['Latitude'],
                    lon=data['Longitude'],
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=10,
                        color=data['Value'],
                        colorscale='thermal',
                        colorbar=dict(title='Salary')
                    ),
                    text=data['title'],
                    hovertemplate=(
                        "<b>Title:</b> %{customdata[0]}<br>"
                        "<b>Employment Type:</b> %{customdata[1]}<br>"
                        "<b>Industry:</b> %{customdata[2]}<br>"
                        "<b>Education:</b> %{customdata[3]}<br>"
                        "<b>Salary High:</b> %{customdata[4]}<br><extra></extra>"
                        "<b>skills:</b> %{customdata[5]}<br><extra></extra>"
                    ),
                    customdata=list(zip(
                        data['title'],
                        data['employment_type'],
                        data['industry'],
                        data['education'],
                        data['salary_high'],
                        data['skills'],
                    ))
                )
            ],
            layout=go.Layout(
                mapbox=dict(
                    style='mapbox://styles/mapbox/dark-v10',
                    accesstoken=env('MAPBOX'),
                    center=center,
                    zoom=5,
                ),
                autosize=True
            )
        ).update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=0,
                pad=0,
            )
        )

        return (
            html.P(location_string),
            figure
        )

    return "No position data available", go.Figure()


# Define the callback function for the pie chart
@app.callback(
    Output('employment-pie-chart', 'figure'),
    [Input('employment-pie-chart', 'clickData')]
)
# Pie chart render
def update_pie_chart(click_data):
    employment_counts = df['employment_type'].value_counts()
    # print(data['employment_type'])
    labels = employment_counts.index.tolist()
    values = employment_counts.values.tolist()

    colors = ['thermal']

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors))]).update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
    return fig

# def generate_3d_scatter(df):
#     fig = px.scatter_3d(df, x='lat', y='lon', z='months_experience', color='industry', symbol='senority')
#
#     # Customize the layout (optional)
#     fig.update_layout(
#         scene=dict(
#             xaxis_title='Latitude',
#             yaxis_title='Longitude',
#             zaxis_title='Months of Experience',
#             bgcolor='rbg(0,0,0,0)',
#         )
#     )
#
#     return fig


# @app.callback(
#     Output('3d-scatter-plot', 'figure'),
#     [Input('map-graph', 'figure')]  # Add other inputs if needed
# )
# def update_3d_scatter(map_figure):
#     return generate_3d_scatter(df)


@app.callback(
    Output("table-container", "children"),
    [Input("state-input", "value")]
)
def update_table(state_input):
    if not state_input:
        return html.P("Please enter state(s) separated by commas.")

    states = [state.strip() for state in state_input.split(",")]

    # Filter data based on user input states
    filtered_data = [d for d in api_data if d["state"].strip().lower() in [state.lower() for state in states]]

    if not filtered_data:
        return html.P("No data available for the entered state(s).")

    table_rows = [
        html.Tr([
            html.Td(d["state"]),
            html.Td(d["index"]),
            html.Td(d["grocery"]),
            html.Td(d["housing"]),
            html.Td(d["utilities"]),
            html.Td(d["transportation"]),
            html.Td(d["health"]),
            html.Td(d["misc"]),
        ])
        for d in filtered_data
    ]

    table = dbc.Table(
        [
            # Table header
            html.Thead([
                html.Tr([
                    html.Th("State"),
                    html.Th("Index"),
                    html.Th("Grocery"),
                    html.Th("Housing"),
                    html.Th("Utilities"),
                    html.Th("Transportation"),
                    html.Th("Health"),
                    html.Th("Misc"),
                ])
            ]),
            # Table body
            html.Tbody(table_rows),
        ],
        bordered=True,
        hover=True,
        responsive=True,
    )

    return table

if __name__ == '__main__':
    app.run_server(debug=True)