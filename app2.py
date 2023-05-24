import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import environ
import psycopg2

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
cursor.execute('SELECT * FROM "public"."skills_skill"')
rows = cursor.fetchall()
cursor.close()
conn.close()

data = {
    "skill": [],
    "jobs": [],
    "pay": [],
}

for row in rows:
    data["skill"].append(row[2])  # Assuming the x-values are in the first column
    data["jobs"].append(row[1])
    if row[0] is None:
        data["pay"].append(100000)
    else:
        data["pay"].append(row[0])  # Salary


skill_data = {
    'Python': [('Software Engineer', 100000), ('Data Scientist', 120000), ('Web Developer', 80000)],
    'Java': [('Software Engineer', 95000), ('Android Developer', 90000), ('Backend Developer', 85000)],
    'JavaScript': [('Web Developer', 90000), ('Frontend Developer', 85000), ('Full-stack Developer', 95000)],
    # Add more skills and their corresponding job and pay data
}




app = dash.Dash(__name__)

# Create the options for the dropdown menu
dropdown_options = [{'label': skill, 'value': skill} for skill in data]

# Create the layout of the app
app.layout = html.Div([
    html.H1('Top Jobs and Pay by Skill'),
    html.Div([
        html.Label('Select a Skill'),
        dcc.Dropdown(
            id='skill-dropdown',
            options=dropdown_options,
            value=dropdown_options[0]['value']
        )
    ]),
    html.Div(id='graph-container')
])


# Define the callback function to update the graph based on the selected skill
@app.callback(
    Output('graph-container', 'children'),
    [Input('skill-dropdown', 'value')]
)
def update_graph(skill):
    job_pay_data = data[skill]
    jobs = [job for job, pay in job_pay_data]
    pay = [pay for job, pay in job_pay_data]

    data = [
        go.Bar(
            x=jobs,
            y=pay,
            marker=dict(color='#1f77b4')
        )
    ]

    layout = go.Layout(
        title=f'Top Jobs and Pay for {skill}',
        xaxis=dict(title='Jobs'),
        yaxis=dict(title='Pay')
    )

    figure = go.Figure(data=data, layout=layout)

    return dcc.Graph(figure=figure)


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
