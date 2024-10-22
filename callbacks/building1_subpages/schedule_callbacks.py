# callbacks/building1_subpages/schedule_callbacks.py

from dash import Input, Output, State
from app_instance import app

# Example callback for updating schedule content
@app.callback(
    Output('schedule-content', 'children'),
    Input('building1-update-interval', 'n_intervals')
)
def update_schedule_content(n):
    # Implement logic to update schedule information
    return html.Div([
        html.P(f"Schedule updated at interval {n}")
    ])
