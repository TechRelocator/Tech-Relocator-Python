from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import environ
import dash_bootstrap_components as dbc
import dash

# ENV setup
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env()

conn = psycopg2.connect(
    host=env('DATABASE_HOST'),
    database=env('DATABASE_NAME'),
    user=env('DATABASE_USER'),
    password=env('DATABASE_PASSWORD'),
)

# how we search through the database after connection
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
}

for row in rows:
    data["employment_type"].append(row[1])
    data["industry"].append(row[2])
    data["education"].append(row[6])
    data["title"].append(row[10])  # Assuming the x-values are in the first column
    data["Latitude"].append(row[11])
    data["Longitude"].append(row[12])
    if row[8] is None:
        data["Value"].append(100000)
    else:
        data["Value"].append(row[8]) # Salary
    if row[8] is None:
        data["salary_high"].append(100000)
    else:
        data["salary_high"].append(row[8])

# start app and call in the theme
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# create the layout for the map
app.layout = dbc.Container([
    dbc.Row(
        className='dark-theme',
        style={'backgroundColor': 'black'},
        children=[
            html.H1("Tech Relocator: Tech Jobs Across the US"),
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
                                colorbar=dict(title='Value')
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
        className='dark-theme',
        style={'backgroundColor': 'black'},
        children=[
                dbc.Col(
                    dcc.Graph(id='employment-pie-chart')
                )]
        )
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
                        colorbar=dict(title='Value')
                    ),
                    text=data['title'],
                    hovertemplate=(
                        "<b>Title:</b> %{customdata[0]}<br>"
                        "<b>Employment Type:</b> %{customdata[1]}<br>"
                        "<b>Industry:</b> %{customdata[2]}<br>"
                        "<b>Education:</b> %{customdata[3]}<br>"
                        "<b>Salary High:</b> %{customdata[4]}<br><extra></extra>"
                    ),
                    customdata=list(zip(
                        data['title'],
                        data['employment_type'],
                        data['industry'],
                        data['education'],
                        data['salary_high']
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
            html.P(f"As of {date} your location was: lat {lat}, lon {lon}, accuracy {pos['accuracy']} meters"),
            figure
        )

    return "No position data available", go.Figure()


# Define the callback function for the pie chart
@app.callback(
    Output('employment-pie-chart', 'figure'),
    [Input('employment-pie-chart', 'clickData')]
)
def update_pie_chart(click_data):
    employment_counts = data['employment_type'].value_counts()
    print(data['employment_type'])
    labels = employment_counts.index.tolist()
    values = employment_counts.values.tolist()

    colors = ['darkblue', 'green', 'black']

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors))]).update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
    return fig



if __name__ == '__main__':
    app.run_server(debug=True)
