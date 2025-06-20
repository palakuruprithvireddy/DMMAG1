import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Load Data
df = pd.read_excel("Final_updated_enslaver_data.xlsx", engine='openpyxl')

# Clean and preprocess the 'enslaved_age' column for the bubble chart
def clean_enslaved_age(df):
    df['enslaved_age'] = pd.to_numeric(df['enslaved_age'], errors='coerce')
    df['enslaved_age'] = df['enslaved_age'].fillna(0)
    df['age_group'] = pd.cut(df['enslaved_age'],
                             bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                             labels=['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100'],
                             right=False)
    df['age_group'] = df['age_group'].cat.add_categories(['Unknown'])
    df.loc[df['enslaved_age'] == 0, 'age_group'] = 'Unknown'
    return df

# Apply the cleaning function
df = clean_enslaved_age(df)

# Initialize Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Interactive Dashboard", style={'textAlign': 'center'}),

    # Filters row
    html.Div([
        dcc.Dropdown(
            id='enslaver_filter',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': enslaver, 'value': enslaver} for enslaver in df['enslaver'].dropna().unique()],
            value=None,
            placeholder="Select an Enslaver",
            style={'width': '45%', 'marginRight': '10px'}
        ),
        dcc.Dropdown(
            id='data_source_filter',
            options=[{'label': 'All', 'value': 'All'}] + [{'label': src, 'value': src} for src in df['data_source'].dropna().unique()],
            value=None,
            placeholder="Select a Data Source",
            style={'width': '45%'}
        )
    ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '20px'}),

    # Graphs
    dcc.Graph(id='bar_chart'),
    dcc.Graph(id='doughnut_chart'),
    dcc.Graph(id='age_bubble_chart'),

    # Enslaved names list
    html.Div(id='enslaved_names_list', style={
        'margin': '20px auto',
        'width': '80%',
        'padding': '10px',
        'border': '1px solid #ccc',
        'borderRadius': '8px',
        'maxHeight': '300px',
        'overflowY': 'scroll',
        'backgroundColor': '#f9f9f9'
    })
])

# Callback
@app.callback(
    [Output('bar_chart', 'figure'),
     Output('doughnut_chart', 'figure'),
     Output('age_bubble_chart', 'figure'),
     Output('enslaved_names_list', 'children')],
    [Input('enslaver_filter', 'value'),
     Input('data_source_filter', 'value')]
)
def update_charts(selected_enslaver, selected_data_source):
    filtered_df = df.copy()

    if selected_enslaver and selected_enslaver != 'All':
        filtered_df = filtered_df[filtered_df['enslaver'] == selected_enslaver]

    if selected_data_source and selected_data_source != 'All':
        filtered_df = filtered_df[filtered_df['data_source'] == selected_data_source]

    # Bar Chart
    enslaver_counts = filtered_df.groupby('enslaver')['enslaved_name'].count().reset_index()
    enslaver_counts = enslaver_counts.sort_values(by='enslaved_name', ascending=False)
    bar_fig = px.bar(
        enslaver_counts, x='enslaver', y='enslaved_name',
        labels={'enslaver': 'Enslaver', 'enslaved_name': 'Number of Enslaved People'},
         #title="Total Count of Enslaved People by Enslaver Names",
        title=(
        "Total Count of Enslaved People by Enslaver Names<br>"
        "<span style='font-size:14px; font-style:italic;'>"
        "Note: Total count assessed from Troy Records and 1850 Slave Schedule may include some duplication where individuals appear in both sources.</span>"
        ),
        text='enslaved_name'
    )
    bar_fig.update_traces(texttemplate='%{text}', textposition='outside')


    # Doughnut Chart
    gender_counts = filtered_df['enslaved_genagedesc'].value_counts().reset_index()
    gender_counts.columns = ['enslaved_genagedesc', 'count']
    doughnut_fig = px.pie(
        gender_counts, names='enslaved_genagedesc', values='count',
        title="Distribution of Enslaved People by Gender Description",
        hole=0.4
    )
    doughnut_fig.update_traces(textinfo='percent+label')

    # Bubble Chart
    age_counts = filtered_df['age_group'].value_counts().reset_index()
    age_counts.columns = ['age_group', 'count']
    bubble_fig = px.scatter(
        age_counts, x='age_group', y=[0]*len(age_counts),
        size='count', color='age_group', hover_name='age_group',
        title="Distribution of Enslaved People by Age Group",
        size_max=60
    )
    bubble_fig.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))
    bubble_fig.update_layout(showlegend=False)

    # Enslaved Name List
    enslaved_names = filtered_df['enslaved_name'].dropna().unique()
    enslaved_list = [html.P(name) for name in enslaved_names]
    title_text = f"Enslaved People Listed by Name under {selected_enslaver}" if selected_enslaver and selected_enslaver != 'All' else "Enslaved People Listed by Name (All Records)"
    enslaved_names_div = html.Div([html.H4(title_text)] + enslaved_list)

    return bar_fig, doughnut_fig, bubble_fig, enslaved_names_div

# Run server
if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
