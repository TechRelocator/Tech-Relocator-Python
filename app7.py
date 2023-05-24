import plotly.express as px
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import environ
import psycopg2
import dash_bootstrap_components as dbc
# Create the initial figure object


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
cursor.execute('SELECT * FROM "public"."job_data_job" LIMIT 100')
rows = cursor.fetchall()
cursor.close()
conn.close()

data = {
    "id": [],
    "employment_type": [],
    "industry": [],
    "job_function": [],
    "senority": [],
    "location": [],
    "education": [],
    "months_experience": [],
    "salary_high": [],
    "salary_low": [],
    "title": [],
    "lat": [],
    "lon": [],

}

for row in rows:
    data["id"].append(row[0])  # Assuming the x-values are in the first column
    data["employment_type"].append(row[1])
    data["industry"].append(row[2])
    data["job_function"].append(row[3])
    data["senority"].append(row[4])
    data["location"].append(row[5])
    data["education"].append(row[6])
    data["months_experience"].append(row[7])

    if row[8] is None:
        data["salary_high"].append(100000)
    else:
        data["salary_high"].append(row[8])

    if row[9] is None:
        data["salary_low"].append(100000)
    else:
        data["salary_low"].append(row[9])
        # Salary

    data["title"].append(row[10])
    data["lat"].append(row[11])
    data["lon"].append(row[12])

# Assuming your 'data' list contains the job data
df = pd.DataFrame(data, columns=['id', 'employment_type', 'industry', 'job_function', 'senority', 'location', 'education', 'months_experience', 'salary_high', 'salary_low', 'title', 'lat', 'lon'])


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


fig = go.Figure()

# Customize the layout of the figure
fig.update_layout(
    scene=dict(
        xaxis_title='Latitude',
        yaxis_title='Longitude',
        zaxis_title='Months of Experience'
    )
)

# Define the function to update the figure
def update_3d_scatter():
    fig.data = [
        go.Scatter3d(
            x=df['lat'],
            y=df['lon'],
            z=df['months_experience'],
            mode='markers',
            marker=dict(
                color=df['thermal'],
                symbol=df['senority']
            )
        )
    ]

# Define the layout of the Dash app
app.layout = dbc.Container([
    dbc.Row(
        children=[
            dcc.Graph(id='3d-scatter-plot', figure=fig),
            dcc.Input(id='hidden-input', type='hidden', value='')
        ]
    )
])

# Define the callback function to update the figure
@app.callback(Output('3d-scatter-plot', 'figure'), [Input('hidden-input', 'value')])
def update_figure(value):
    update_3d_scatter()
    return fig

    # Run the Dash app


if __name__ == '__main__':
    app.run_server(debug=True)