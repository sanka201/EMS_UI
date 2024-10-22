# layouts/home_layout.py

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from dash import Input, Output, State, html

#place holder for the bar chart
bar_fig = go.Figure()  
bar_fig.add_trace(go.Bar(x=['Wind '],y=[500],name='latestwind',textfont=dict(color='black',weight='bold',size=16)),)
bar_fig.add_trace(go.Bar(x=['Total load '],y=[3000],name='Total sum',textfont=dict(color='black',weight='bold',size=16),))
bar_fig.add_trace(go.Bar(x=['Groups Consumption '],y=[1000],name='Group1',textfont=dict(color='black',weight='bold',size=16),))
bar_fig.add_trace(go.Bar(x=['Groups Consumption '],y=[1500],name='Group2',textfont=dict(color='black',weight='bold',size=16),))
bar_fig.add_trace(go.Bar(x=['Groups Consumption '],y=[5000],name='Group3',textfont=dict(color='black',weight='bold',size=16),))
bar_fig.update_layout(
    barmode='stack',  # Stack the bars for priority groups
    showlegend=True,)


# Placeholder data for line charts
time_index = pd.date_range(start='2021-01-01', periods=24, freq='H')
total_power_data = np.random.randint(100, 200, size=24)
priority_power_data = np.random.randint(50, 100, size=24)

total_power_df = pd.DataFrame({
    'Time': time_index,
    'Total Power': total_power_data
})

priority_power_df = pd.DataFrame({
    'Time': time_index,
    'Priority Power': priority_power_data
})

# Create line charts
total_power_fig = px.line(total_power_df, x='Time', y='Total Power', title='Total Power Consumption')
priority_power_fig = px.line(priority_power_df, x='Time', y='Priority Power', title='Priority Group Power Consumption')
data_store = dcc.Store(id='home-data-store')
# Define the home layout
home_layout = dbc.Container([data_store,
    html.Div(style={'height': '30px'}),  # Spacer

    # Existing three cards
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.H5([
                        html.I(className="fas fa-chart-bar", id="icon-consumption"),
                        html.Span(" Building Consumption", className='ml-2')
                    ], className='card-title'),
                    className='card-header'
                ),
                dbc.CardBody(
                    dcc.Graph(id='consumption-chart', figure=bar_fig)
                ),
            ], className='card mb-4 shadow'),
            width=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.H5([
                        html.I(className="fas fa-bolt", id="icon-grid-status"),
                        html.Span(" Grid Status", className='ml-2')
                    ], className='card-title'),
                    className='card-header'
                ),
                dbc.CardBody(
                    [html.I(id='grid-status-icon', style={'font-size': '2em', 'margin-right': '10px'}),
                    html.H4(id='grid-status', className='card-text',style={'display': 'inline-block', 'vertical-align': 'middle'})],style={'text-align': 'center'}
                ),
            ], className='card mb-4 shadow'),
            width=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.H5([
                        html.I(className="fas fa-dollar-sign", id="icon-pricing"),
                        html.Span(" Pricing Information", className='ml-2')
                    ], className='card-title'),
                    className='card-header'
                ),
                dbc.CardBody([
                    # Real-time Marginal Price
                    html.Div([
                        html.Span("Real-time Marginal Price: ", className='pricing-label'),
                        html.Span(id='realtime-marginal-price', className='pricing-value'),
                        html.Span(id='realtime-marginal-trend', className='pricing-trend ml-2'),
                    ], className='mb-2'),
                    # Hourly Price
                    html.Div([
                        html.Span("Hourly Price: ", className='pricing-label'),
                        html.Span(id='hourly-price', className='pricing-value'),
                        html.Span(id='hourly-price-trend', className='pricing-trend ml-2'),
                    ], className='mb-2'),
                    # Hourly Cost
                    html.Div([
                        html.Span("Hourly Cost: ", className='pricing-label'),
                        html.Span(id='hourly-cost', className='pricing-value'),
                        html.Span(id='hourly-cost-trend', className='pricing-trend ml-2'),
                    ]),
                ]),
            ], className='card mb-4 shadow'),
            width=4
        ),
    ], className='mb-4'),

    # New cards for the line graphs
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.H5([
                        html.I(className="fas fa-chart-line"),
                        html.Span(" Total Power Consumption", className='ml-2')
                    ], className='card-title'),
                    className='card-header'
                ),
                dbc.CardBody(
                    dcc.Graph(id='total-power-chart', figure=total_power_fig)
                ),
            ], className='card mb-4 shadow'),
            width=12  # Full width
        ),
    ], className='mb-4'),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.H5([
                        html.I(className="fas fa-users"),
                        html.Span(" Priority Group Power Consumption", className='ml-2')
                    ], className='card-title'),
                    className='card-header'
                ),
                dbc.CardBody(
                    dcc.Graph(id='priority-power-chart', figure=priority_power_fig)
                ),
            ], className='card mb-4 shadow'),
            width=12  # Full width
        ),
    ], className='mb-4'),

    # Tooltips for icons
    dbc.Tooltip("Displays the consumption data of buildings.", target="icon-consumption", placement="top"),
    dbc.Tooltip("Shows the current grid status.", target="icon-grid-status", placement="top"),
    dbc.Tooltip("Displays the real-time marginal pricing.", target="icon-pricing", placement="top"),
    dcc.Store(id='prev-realtime-price', data=None),
    dcc.Store(id='prev-hourly-price', data=None),
    dcc.Store(id='prev-hourly-cost', data=None),
    dcc.Interval(
        id='home-update-interval',
        interval=20*1000,  # 40 seconds
        n_intervals=0
    )
], fluid=True)
