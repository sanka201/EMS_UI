# layouts/building1_subpages/devices_layout.py

from dash import html, dcc
import dash_bootstrap_components as dbc
from components.building_navbar import create_building_navbar  # Import the secondary navbar
import plotly.graph_objects as go
building1_navbar = create_building_navbar('GNIREBUILDING540')
import dash
import pandas as pd
from UserInterface.components.devicetable import DeviceTable
# Sample data
 # Example data for 3 devices
 
device_ids = ['Device 1', 'Device 2', 'Device 3','Device 1', 'Device 2', 'Device 3','Device 1', 'Device 2']
current_power = [4,25,39,30, 45, 60,76,64]  # Simulated power values
power_max = [100, 400, 300,100, 400, 700,100, 400]
status_values = [1, 0, 1,1, 0, 1, 0, 1]  # 1 for on, 0 for off
priority_values = [2, 1, 3,2, 1, 3,1, 3]

figdevices=go.Figure()

# Create DataFrame
df = pd.DataFrame({
    'Device ID': device_ids,
    'Power Usage (W)': current_power,
    'Power Max (W)': power_max,
    'Status': ['On' if status == 1 else 'Off' for status in status_values],
    'Priority': priority_values
})


device_card = dbc.Card(
    [ dbc.CardHeader(
        html.H5([
            html.I(className="fas fa-sitemap", id="icon-ev"),
            html.Span(" Device info", className='ml-2')
        ], className='card-title'),
        className='card-header'
    ),
        dbc.CardBody(
            html.Div([
                dcc.Graph(
                            id='device-table',
                           figure=DeviceTable(df),config={'responsive': True},  # Make it responsive
                    style={'height': '100%', 'width': '100%'} 
                        )
            ], className='battery-container flex-row' , style={'width':'100%', 'padding': '0px', 'margin': '5px'})  # Add flex-row class for horizontal alignment
        ),
    ],
    className="mb-4 shadow  ", style={'padding': '0px', 'margin': '20px'},
)

device_fig_card = dbc.Card(
    [ dbc.CardHeader(
        html.H5([
            html.I(className="fas fa-sitemap", id="icon-ev"),
            html.Span(" Devices power consumption", className='ml-2')
        ], className='card-title'),
        className='card-header'
    ),
        dbc.CardBody(
            html.Div([
                dcc.Graph(
                            id='devices-figure',
                           figure=figdevices,config={'responsive': True},  # Make it responsive
                    style={'height': '100%', 'width': '100%'} 
                        )
            ], className='battery-container flex-row' , style={'width':'100%', 'padding': '0px', 'margin': '5px'})  # Add flex-row class for horizontal alignment
        ),
    ],
    className="mb-4 shadow  ", style={'padding': '0px', 'margin': '20px'},
)


data_store = dcc.Store(id='gnire-building-540-data-store')
devices_layout = html.Div([
    building1_navbar,
    data_store,
    html.H3("Building 1 - Devices Info"),
    # Add components specific to Devices Info
    # For example, a table or graphs showing device statuses
    html.Div(id='devices-content'), 
    html.Div(device_card),
    html.Div(device_fig_card),  
   
        # Include the Interval component if not already included
    dcc.Interval(
        id='nire-building-540-update-interval',
        interval=10*1000,  # Update every minute
        n_intervals=0
    ),
])
