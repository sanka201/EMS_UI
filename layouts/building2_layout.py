import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import pandas as pd
import random
from components.building_navbar import create_building_navbar  # Import the secondary navbar
import plotly.graph_objects as go
from app_instance import app

# Sample data for energy consumption over time
consumption_time_data = pd.DataFrame({
    'Timestamp': pd.date_range(start='2021-01-01', periods=24, freq='H'),
    'Consumption': [random.uniform(50, 150) for _ in range(24)]
})

# Create the line chart
consumption_time_fig = px.line(
    consumption_time_data,
    x='Timestamp',
    y='Consumption',
    title='Energy Consumption Over Time',
    labels={'Timestamp': 'Time', 'Consumption': 'Consumption (kWh)'}
)

consumption_time_fig.update_layout(
    margin=dict(l=20, r=20, t=50, b=20),
    paper_bgcolor='white',
    plot_bgcolor='white',
    hovermode='x unified'
)

# Energy Consumption Over Time Card
energy_generation_card = dbc.Card([
    dbc.CardHeader(
        html.H5( [html.I(className="fas fa-solar-panel", id="icon-energy-com"), html.Span(" Energy Generation Over Time", className='card-title')] ),
        className='card-header' ,   style={
                "background-color": "#74d600",  # Set the header background color to #ff9a00
                "color": "white"  # Optional: Set the text color to white for better contrast
            }
    ),
    dbc.CardBody(
        dcc.Graph(
            id='generation-time-chart',
            figure=consumption_time_fig
        )
    ),
], className='card mb-4 shadow',  style={
        "border": "2px solid #028900",  # You can change 'blue' to your desired border color
        "border-radius": "10px"  # Optional: Adjust the corner radius if desired
    }
)

# Energy Consumption Over Time Card
lmp_time_card = dbc.Card([
    dbc.CardHeader(
        html.H5( [html.I(className="fas fa-balance-scale", id="icon-energy-com"), html.Span(" LMP  Over Time", className='card-title')]),
        className='card-header' ,   style={
                "background-color": "#74d600",  # Set the header background color to #ff9a00
                "color": "white"  # Optional: Set the text color to white for better contrast
            }
    ),
    dbc.CardBody(
        dcc.Graph(
            id='building2-lmp-time-chart',
            figure=consumption_time_fig
        )
    ),
], className='card mb-4 shadow',  style={
        "border": "2px solid #028900",  # You can change 'blue' to your desired border color
        "border-radius": "10px"  # Optional: Adjust the corner radius if desired
    })


# Energy Consumption Over Time Card
consumption_time_card = dbc.Card([
    dbc.CardHeader(
        html.H5([html.I(className="fas fa-chart-line", id="icon-energy-com"), html.Span(" Energy Consumption Over Time", className='card-title')]),
        className='card-header',   style={
                "background-color": "#74d600",  # Set the header background color to #ff9a00
                "color": "white"  # Optional: Set the text color to white for better contrast
            }
    ),
    dbc.CardBody(
        dcc.Graph(
            id='building2-consumption-time-chart',
            figure=consumption_time_fig
        )
    ),
], className='card mb-4 shadow',  style={
        "border": "2px solid #028900",  # You can change 'blue' to your desired border color
        "border-radius": "10px"  # Optional: Adjust the corner radius if desired
    })


# Energy Production vs. Consumption Card
production_consumption_card = dbc.Card([
    dbc.CardHeader(
        html.H5([html.I(className="fas fa-layer-group", id="icon-energy-com"), html.Span(" Priority Group Consumption", className='card-title')]),
        className='card-header',   style={
                "background-color": "#74d600",  # Set the header background color to #ff9a00
                "color": "white"  # Optional: Set the text color to white for better contrast
            }
    ), 
    dbc.CardBody(
        dcc.Graph(
            id='building2-priority-consumption-chart',
            figure=consumption_time_fig
        )
    ),
], className='card mb-4 shadow',  style={
        "border": "2px solid #028900",  # You can change 'blue' to your desired border color
        "border-radius": "10px"  # Optional: Adjust the corner radius if desired
    })




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

# EV Card using Flexbox Layout
ev_card = dbc.Card([
    dbc.CardHeader(
        html.H5([
            html.I(className="fas fa-car", id="icon-ev"),
            html.Span(" Electric Vehicale Emmulator", className='ml-2')
        ], className='card-title'),
        className='card-header',  style={
                "background-color": "#74d600",  # Set the header background color to #ff9a00
                "color": "white"  # Optional: Set the text color to white for better contrast
            }
    ),
    dbc.CardBody(
        html.Div([
            # EV Image
            html.Img(
                src=app.get_asset_url('ev_image.jpg'),
                id='ev-image',
                className='ev-image'
            ),
            # EV Status with Icon using Flexbox
            html.Div([
                html.I(id='ev-status-icon'),
                html.Span(id='building2-ev-status')
            ], className='ev-status-flex'),
            # EV Battery Level
            html.P(id='building2-ev-battery-level', className='card-text'),
        ], className='min-height-ev-card ev-container'),
    ) ,
], className= 'mb-4 shadow',   style={
        "border": "2px solid #028900",  # You can change 'blue' to your desired border color
        "border-radius": "10px"  # Optional: Adjust the corner radius if desired
    })

pricing_card = dbc.Card([
    dbc.CardHeader(
        html.H5([
            html.I(className="fas fa-dollar-sign", id="icon-pricing"),
            html.Span(" Pricing Information", className='ml-2')
        ], className='card-title'),
        className='card-header',  style={
                "background-color": "#74d600",  # Set the header background color to #ff9a00
                "color": "white"  # Optional: Set the text color to white for better contrast
            }
    ),
    dbc.CardBody([
        # Real-time Marginal Price
        html.Div([
            html.Span("Real-time Marginal Price: ", className='pricing-label'),
            html.Span(id='building2-realtime-marginal-price', className='pricing-value'),
            html.Span(id='building2-realtime-marginal-trend', className='pricing-trend ml-2'),
        ], className='mb-2'),
        # Hourly Price
        html.Div([
            html.Span("Hourly Price: ", className='pricing-label'),
            html.Span(id='building2-hourly-price', className='pricing-value'),
            html.Span(id='building2-hourly-price-trend', className='pricing-trend ml-2'),
        ], className='mb-2'),
        # Hourly Cost
        html.Div([
            html.Span("Hourly Cost: ", className='pricing-label'),
            html.Span(id='building2-hourly-cost', className='pricing-value'),
            html.Span(id='building2-hourly-cost-trend', className='pricing-trend ml-2'),
        ]),
    ]),
], className='card mb-4 shadow', style={
        "border": "2px solid #028900",  # You can change 'blue' to your desired border color
        "border-radius": "10px"  # Optional: Adjust the corner radius if desired
    })


# Consumption Information Card
consumption_card = dbc.Card([
    dbc.CardHeader(
        html.H5([
            html.I(className="fas fa-chart-pie", id="icon-consumption"),
            html.Span(" Consumption and Generation Information", className='ml-2')
        ], className='card-title'),
        className='card-header',  style={
                "background-color": "#74d600",  # Set the header background color to #ff9a00
                "color": "white"  # Optional: Set the text color to white for better contrast
            }
    ),
    dbc.CardBody(
        dcc.Graph(id='building2-consumption-bar', figure=bar_fig)
    ),
], className='card mb-4 shadow', style={
        "border": "2px solid #028900",  # You can change 'blue' to your desired border color
        "border-radius": "10px"  # Optional: Adjust the corner radius if desired
    }
)

# Create the secondary navigation bar
building2_navbar = create_building_navbar('GLEAMM')
# Include a dcc.Store component
data_store = dcc.Store(id='building2-data-store')

building2_layout = dbc.Container([
     html.Div(style={'height': '30px'}),  # Spacer
    # Include the secondary navigation bar
    building2_navbar,
    data_store,
    
    dbc.Row([
                dbc.Col(ev_card,width=4),
                dbc.Col(pricing_card, width=4),
                dbc.Col( consumption_card, width=4)
    ], className='mb-4'),
    # Add more components specific to Building 2
       # Row with the two new chart cards
    dbc.Row([
        dbc.Col(
            consumption_time_card,
            width=6
        ),
        dbc.Col(
            production_consumption_card,
            width=6
        ),
    ], className='mb-4'),
    
   # Row with the two new chart cards
    dbc.Row([
        dbc.Col(
            energy_generation_card,
            width=6
        ),
        dbc.Col(
            lmp_time_card,
            width=6
        ),
    ], className='mb-4'),
    # Include the Interval component if not already included
    dcc.Interval(
        id='building2-update-interval',
        interval=10*1000,  # Update every minute
        n_intervals=0
    ),
], fluid=True)