# Import all the modules
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from flask import Flask

# Import and clean data
df = pd.read_csv('https://raw.githubusercontent.com/kjyu1292/003/main/traffic-volume-counts.csv').fillna(0)
df['Date'] = pd.to_datetime(df['Date'])
df['year'] = df.Date.dt.year

df['x'] = np.where(
    (df['road_type'].str.contains('av|nue', regex = True)) | 
    (df['road_type'].isin(['u', 'p', 'z', 'm', 'j', 'n', 'e', 'l'])), 'avenue', df['road_type']
)
df['x'] = np.where(df['road_type'].str.contains('bl|be|bou'), 'boulevard', df['x'])
df['x'] = np.where(df['road_type'].isin(['street', 'st', 'sr']), 'street', df['x'])
df['x'] = np.where(df['road_type'].str.contains('pkwy|park'), 'parkway', df['x'])
df['x'] = np.where(df['road_type'].str.contains('concourse'), 'concourse', df['x'])
df['x'] = np.where(df['road_type'].str.contains('dr'), 'concourse', df['x'])
df['x'] = np.where(df['road_type'].isin(['rd', 'road', 'roadway']), 'road', df['x'])
df['x'] = np.where(df['road_type'].isin(['expressway', 'expresspway']), 'expressway', df['x'])

df['road_type'] = df['x']
df.drop(['x'], axis = 1, inplace = True)

# Initiate the App
server = Flask(__name__)
app = Dash(__name__, 
           server = server, 
           external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

# Prepare Component
## Header
Header_component = html.H1("Traffic Analysis Dashboard", style = {'text-align': 'center', 'color': 'darkcyan'})
## Dataframe for component 1
c1 = df.groupby(['year', 'road_type', 'Roadway Name'])[['ID']] \
       .agg('count').reset_index().sort_values(by = ['year', 'ID'], ascending = [True, False])
## Dataframe for component 2
c2 = df.groupby('year')[[str(i) for i in range (1, 25)]].agg('sum').T \
       .reset_index().rename({'index': 'hour'}, axis = 1).astype(np.int64)

# Design
## App Layout
app.layout = html.Div(
    [
        dbc.Row([Header_component]),
        html.H3(
            "Tree Map of # traffic flows grouping by types of road",
            style = {'text-align': 'left', 
                     'color': 'navy',
                     'font-weight': 'bold',
                     'font-style': 'italic'}
        ),
        dbc.Row(
            [
                dbc.Col(html.P('Choose # most common roads:', style = {'text-align': 'right'})),
                dbc.Col(dcc.Input(
                    id = "input_fig1_num",
                    type = 'number',
                    placeholder = "input type number",
                    value = 50,
                    style = {'width': '200px'}
                ))
            ]
        ),
        html.Div(
            [dcc.Graph(id = 'fig1', figure = {})], 
            style = {"width": "95%", "display":"inline-block","position":"relative"}
        ),
        html.Div([
            dcc.RangeSlider(
                id = "input_fig1_range",
                min = 2012, max = 2021, step = 1,
                value = [2015, 2018],
                allowCross = False,
                marks = {i: str(i) for i in range (2012, 2022)},
                vertical = True
             )], 
            style = {"width": "5%", "height":"100%","display":"inline-block","position":"relative"}
        ),
        html.H3(
            "Hourly Volume Trend by Year",
            style = {'text-align': 'left', 
                     'color': 'navy',
                     'font-weight': 'bold',
                     'font-style': 'italic'}
        ),
        dcc.Graph(id = 'fig2', figure = {})
    ]
)
## Callback
@app.callback(
    [
        Output(component_id = 'fig1', component_property = 'figure'),
        Output(component_id = 'fig2', component_property = 'figure')
    ],
    [
        Input(component_id = 'input_fig1_range', component_property = 'value'),
        Input(component_id = 'input_fig1_num', component_property = 'value')
    ]
)

def update_graph(selected_year, n):
    
    fig1 = px.treemap(
        c1[c1.year.isin(selected_year)].groupby(['road_type', 'Roadway Name'])[['ID']] \
            .agg('sum').reset_index().sort_values(by = 'ID', ascending = False).head(n), 
        path = ['road_type', 'Roadway Name'], 
        values = 'ID'
    )
    fig1.update_traces(textinfo = 'label+text+value')
    fig1.update_layout(margin = dict(t=30, l=0, r=0, b=10))
    
    fig2 = go.Figure()
    for i in [x for x in range (2012, 2022)]:
        fig2.add_trace(go.Scatter(x = c2.hour, y = c2[i], mode = 'lines', name = i))
    fig2.update_layout(xaxis = dict(title = '<b>Hour<b>', tickmode='linear'),
                       yaxis = dict(title = '<b>Volume<b>'),
                       legend_title_text = '<b>Year<b>')
    
    return fig1, fig2

# Run the app
if __name__ == '__main__':
    app.run_server(debug = True)