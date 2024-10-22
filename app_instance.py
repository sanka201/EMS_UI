from flask import Flask
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# Initialize Flask server
server = Flask(__name__)

# Initialize Dash app
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css?family=Open+Sans&display=swap',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'  # Font Awesome

    ],
    suppress_callback_exceptions=True
)
