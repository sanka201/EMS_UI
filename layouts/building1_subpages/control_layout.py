# layouts/building1_subpages/control_layout.py

from dash import html, dcc
import dash_bootstrap_components as dbc
from components.building_navbar import create_building_navbar  # Import the secondary navbar
import plotly.graph_objects as go
building1_navbar = create_building_navbar('GNIREBUILDING540')
control_layout = html.Div([
    building1_navbar,
    html.H3("Building 1 - Control"),
    # Add components specific to Control
    # For example, control panels or buttons
    html.Div(id='control-content')
])
