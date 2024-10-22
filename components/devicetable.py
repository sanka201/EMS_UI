import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd

def DeviceTable(df):

    df = df.sort_values(by='Priority', ascending=False)
    # Add a column for status with indicators
    #df['Status'] = ['🟢 On' if status == 'On' else '🔴 Off' for status in df['Status']]
    
    # Create a custom column with text-based progress bars
   # Create a custom column with text-based progress bars
    try:
# Properly formatting the "Power Usage (W)" column with a bar display
        df['Power Usage (W)'] = [
            f'{power}W \t \t \t' + '█ ' * int(round((power / max_power), 1) * 10) + '░ ' * int(round((1 - (power / max_power)), 1) * 10)
            if max_power > 0 else f'{power}W'
            for power, max_power in zip(df['Power Usage (W)'], df['Power Max (W)'])
        ]

    except  Exception as e:
       print(e)
    # Create the table figure using plotly.graph_objs.Table
    fig = go.Figure(data=[go.Table(
        header=dict(
        values=list(df.columns),
        fill_color='lightgrey',
        align='center',
        font=dict(color='black', size=18, weight='bold'),
        height=40,
         line_color='gray',
        ),
        cells=dict(
        values=[df[col] for col in df.columns],
        align=['left' if col == 'Power Usage (W)' else 'center' ''for col in df.columns],
        fill_color='white',
        font=dict(color='black', size=18, weight='bold'),
        height=40,
         line_color='gray',
        )
    )])
    
    fig.update_layout(
    height=len(df)*45  # Set the height to 600 pixels
        )

    return fig
