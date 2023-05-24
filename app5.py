import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd

import plotly.graph_objs as go
import plotly.express as px
import environ
import psycopg2
import requests

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


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('Job Search'),
    dcc.Input(id='skill-input', type='text', placeholder='Enter a skill'),
    html.Button('Search', id='search-button'),
    html.Div(id='job-table-container')
])


@app.callback(
    dash.dependencies.Output('job-table-container', 'children'),
    [dash.dependencies.Input('search-button', 'n_clicks')],
    [dash.dependencies.State('skill-input', 'value')]
)
def update_job_table(n_clicks, skill):
    if n_clicks is not None and skill:
        # Make a request to your backend API using the entered skill
        api_url = f'https://tech-relocator-backend-4436gsx7g-tech-relocator.vercel.app/api/v1/skills/?search={skill}'
        response = requests.get(api_url)

        if response.status_code == 200:
            jobs = response.json()
            # Assuming your API response is a list of job objects
            df = pd.DataFrame(jobs)
            # Create a table from the fetched job data
            table = html.Table(
                # Create the table header
                [html.Tr([html.Th(col) for col in df.columns])] +
                # Create the table rows
                [html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(len(df))]
            )
            return table
        else:
            return 'Error: Failed to fetch job data'


if __name__ == '__main__':
    app.run_server(debug=True)
