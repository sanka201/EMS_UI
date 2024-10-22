# app.py

from flask import Flask
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# Import 'app' and 'server' from 'app_instance.py'
from app_instance import app, server
# Import layouts
from layouts.home_layout import home_layout
from UserInterface.layouts.building1_layout import building1_layout
from UserInterface.layouts.building1_subpages.control_layout import control_layout
from UserInterface.layouts.building1_subpages.schedule_layout import schedule_layout
from UserInterface.layouts.building1_subpages.devices_layout import devices_layout
from layouts.building2_layout import building2_layout

# Import the navigation bar
from components.navigation import navbar
# Define the app layout with the navigation bar and page content

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,  # Include the navigation bar here
    html.Div(id='page-content')
])


# app.py (continued)
from callbacks import home_callbacks, building1_callbacks, building2_callbacks
from callbacks.building1_subpages import devices_callbacks, schedule_callbacks, control_callbacks
# Update the page content based on URL
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return home_layout
    elif pathname == '/GNIREBUILDING540':
        return building1_layout
    elif pathname == '/building2':
        return building2_layout
    elif pathname =='/GNIREBUILDING540/devices':
        return devices_layout
    elif pathname =='/GNIREBUILDING540/schedule':
        return schedule_layout
    elif pathname =='/GNIREBUILDING540/control':
        return control_layout
    else:
        print(pathname)
        return html.H1('404 Page Not Found1')




if __name__ == '__main__':
    app.run_server(debug=True,host='192.168.10.254',port=8051)
