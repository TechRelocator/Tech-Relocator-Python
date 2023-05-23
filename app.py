from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import environ

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
    "Value": []
}

for row in rows:
    data["title"].append(row[10])  # Assuming the x-values are in the first column
    data["Latitude"].append(row[11])
    data["Longitude"].append(row[12])
    if row[8] is None:
        data["Value"].append(100000)
    else:
        data["Value"].append(row[8])  # Salary

# Sample data
# data = pd.DataFrame({
#     'title': ['New York', 'Los Angeles', 'Chicago'],
#     'Latitude': [40.7128, 34.0522, 41.8781],
#     'Longitude': [-74.0060, -118.2437, -87.6298],
#     'Value': [100, 200, 300]
# })

# csv with multiple columns, headers
# df = pd.DataFrame(data)

app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1("Map with Data Overlay"),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Scattermapbox(
                        lat=data['Latitude'],
                        lon=data['Longitude'],
                        mode='markers',
                        marker=go.scattermapbox.Marker(
                            size=10,
                            color=data['Value'],
                            colorscale='Blues',
                            colorbar=dict(title='Value')
                        ),
                        text=data['title']
                    )
                ],
                layout=go.Layout(
                    title='Map with Data Overlay',
                    mapbox=dict(
                        accesstoken=env('MAPBOX'),
                        center=dict(lat=39, lon=-98),
                        zoom=3
                    ),
                    autosize=True
                )
            )
        )
    ]
)





# app.layout = html.Div([
#     html.H1(children='Title of Dash App', style={'textAlign':'center'}),
#
#     # Pick out one column for the dropdown, with Canada as the default selection
#     dcc.Dropdown(df.title.unique(), 'Senior Data Engineer', id='dropdown-selection'),
#
#     # Creates graph
#     dcc.Graph(id='graph-content')
# ])

# @callback(
#     Output('graph-content', 'figure'),
#     Input('dropdown-selection', 'value')
# )

def update_graph(value):
    # Choose the base dataset filtered by country
    dff = df[df.title==value]
    # Choose X / Y Axis data
    return px.line(dff, x='title', y='salary')

if __name__ == '__main__':
    app.run_server(debug=False)
