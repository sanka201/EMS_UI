# callbacks/building2_callbacks.py
from dash import Input, Output, State, html
from app_instance import app
import random
import pandas as pd
import plotly.express as px
import mysql.connector
import json
from datetime import datetime,timedelta
from dash import Input, Output, State, html
from app_instance import app
from db_connection import get_connection
import json
from pandas import json_normalize
import pandas as pd
from UserInterface.components.devicetable import DeviceTable
import plotly.graph_objects as go



# Helper function to guess missing threshold values
def guess_missing_thresholds(thresholds_list):
    last_thresholds = None
    for i, thresholds in enumerate(thresholds_list):
        if thresholds is None:
            if last_thresholds is not None:
                thresholds_list[i] = last_thresholds
        else:
            last_thresholds = thresholds
    return thresholds_list

def guess_missing_thresholds_spit(control_commands):
    priority_thresholds = {}
    total_thresholds = []
    last_priority_thresholds = None
    last_total_threshold = None
    for command in control_commands:
        if isinstance(command, dict):
            current_priority_thresholds = {priority: cmd[1] for priority, cmd in command.items()}
            last_priority_thresholds = current_priority_thresholds
            total_thresholds.append(sum(cmd[1] for cmd in command.values()))
        elif isinstance(command, list) and len(command) == 2:
            last_total_threshold = command[1]
            current_priority_thresholds = None
            total_thresholds.append(last_total_threshold)
        else:
             current_priority_thresholds = last_priority_thresholds
             total_thresholds.append(last_total_threshold)

        # Update the priority thresholds dictionary
        if current_priority_thresholds:
            for priority, threshold in current_priority_thresholds.items():
                if priority not in priority_thresholds:
                    priority_thresholds[priority] = []
                priority_thresholds[priority].append(threshold)
        else:
           
            for priority in priority_thresholds:
                priority_thresholds[priority].append(None)

    # Insert the latest thresholds at the end of the lists
    if last_priority_thresholds:
        for priority, threshold in last_priority_thresholds.items():
            if priority in priority_thresholds:
                priority_thresholds[priority][-1] = threshold
            else:
                priority_thresholds[priority] = [threshold]
    
    if last_total_threshold is not None:
        total_thresholds[-1] = last_total_threshold
    # for priority in priority_thresholds:
    #     priority_thresholds[priority].reverse()
    #total_thresholds.reverse()
    return priority_thresholds, total_thresholds

@app.callback(
    Output('building2-data-store', 'data'),
    Input('building2-update-interval', 'n_intervals')
)

def query_database(n_intervals):
    # Fetch data from the database
    conn = None
    cursor = None
    try:
        conn,conn2 = get_connection()
        cursor = conn.cursor()

        # Query to get all necessary data
        query =""" SELECT ts, value_string FROM GLEAMM_NIRE.data  where topic_id=8 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 3 hour) ORDER BY ts DESC """

        cursor.execute(query)

        result = cursor.fetchall()

        data_list = []
        for row in result:
            ts, value_string = row
            tempdata = json.loads(value_string)
            data_list.append((ts, tempdata))
            
        # Extract control commands and guess missing thresholds
        control_commands = [data.get('Control', {}).get('GLEAMM', {}).get('cmd', None) for _, data in data_list]
# Flatten the JSON for each (timestamp, data) pair and add the timestamp as a column        


       
        LMP = data_list[0][1]['LMP']
        one_hour_ago=data_list[0][0]-timedelta(hours=1)
        filtered_tuples = [tup[1]['LMP'] for tup in data_list if tup[0] >= one_hour_ago]
        LMP_average_for_last_hour=sum(filtered_tuples)/1000/len(filtered_tuples)
        lmptrend = [round(tup[1]['LMP']/1000,3) for tup in data_list ]
        guessed_commands = guess_missing_thresholds(control_commands)
        
        
        # Parse thresholds and prepare for display
        thresholds_list = []
        combined_threshold = None
        for command in guessed_commands:
            if isinstance(command, list) and len(command) == 2:
                thresholds_list.append({'total': command[1]})
                combined_threshold = command[1]  # Use this as the total consumption threshold
            elif isinstance(command, dict):
                thresholds_list.append({priority: cmd[1] for priority, cmd in command.items()})
                combined_threshold = sum(cmd[1] for cmd in command.values())  # Combine thresholds for total consumption
            else:
                thresholds_list.append(None)

        guessed_thresholds_list = guess_missing_thresholds(thresholds_list)
        
        # Prepare display for thresholds
        if guessed_thresholds_list[0]:
            if 'total' in guessed_thresholds_list[0]:
                thresholds_display = f"Current Threshold: Total Consumption <= {guessed_thresholds_list[0]['total']} W"
            else:
                thresholds_display = "Current Thresholds: " + ", ".join(
                    [f"Priority {priority} <= {threshold} W" for priority, threshold in guessed_thresholds_list[0].items()]
                )
        else:
            thresholds_display = "No valid threshold command available."
            
        priority_thresholds_list, total_thresholds_list=guess_missing_thresholds_spit(control_commands[::-1])

        # Process data for total consumption and priority consumption
        priority_trend_list = []
        latest_data = data_list[0]
        Evlatest=[]
        for ts, data in data_list:
            for monitor, buildings in data.get('Monitor', {}).items():
                for building, devices in buildings.items():
                    for device, metrics in devices.items():
                        priority_trend_list.append({
                            'timestamp': ts,
                            'priority': metrics.get('priority'),
                            'power': metrics.get('power')
                        })
                        
        data = {
            'dbconnectivity' : 'online',
            'LMP':round(LMP/1000,3),
            'LMPhr': round(sum(filtered_tuples)/1000/len(filtered_tuples),3),
            'Evstatus': 'Not configured',
            'EvPower': None,
            'Evenergy': None,
            'prioritytrend': priority_trend_list,
            'thresholdlist': total_thresholds_list,
            'priority_thresholds_list':priority_thresholds_list,
            'lmptrend':lmptrend[::-1]
            }
    except:
        data = {
            'dbconnectivity' : 'error'
        }
    finally:
        cursor.close()
        conn.close()
            
    return data


# Callback to update real-time marginal price
@app.callback(
    [Output('building2-realtime-marginal-price', 'children'),
     Output('building2-realtime-marginal-trend', 'children'),
     Output('building2-hourly-price', 'children'),
     Output('building2-hourly-price-trend', 'children')],
    [Input('building2-data-store', 'data')]
)
def update_realtime_marginal_price(data):
    # Simulate price data
    price=data.get('LMP', 0)
    trend_icon = html.I(className='fas fa-arrow-up', style={'color': 'green'}) if random.choice([True, False]) else html.I(className='fas fa-arrow-down', style={'color': 'red'})
    hrprice=data.get('LMPhr', 0)
    hrtrend_icon = html.I(className='fas fa-arrow-up', style={'color': 'green'}) if random.choice([True, False]) else html.I(className='fas fa-arrow-down', style={'color': 'red'})

    
    return f"${price}/kWh", trend_icon,f"${hrprice}/kWh", hrtrend_icon



@app.callback(
     [Output('building2-consumption-time-chart', 'figure'),Output('building2-lmp-time-chart', 'figure'), Output('building2-priority-consumption-chart','figure'), Output("building2-consumption-bar","figure")],
    Input('building2-data-store', 'data')
)
def update_consumption_time_chart(data):
        lmptrend = data['lmptrend']
        trend=pd.DataFrame( data['prioritytrend'])
        threshold=data['thresholdlist']
        priority_thresholds_list=data['priority_thresholds_list']
        df_priority_grouped = trend.groupby(['timestamp', 'priority']).sum().reset_index()    
        df_total_consumption = df_priority_grouped.groupby('timestamp').sum().reset_index()
        latest_time=df_total_consumption['timestamp'].iloc[-1]
        df_total_consumption['Threshold']=threshold
        latest_threh= threshold[-1]
        latest_power= round(df_total_consumption['power'].iloc[-1])
        latest_value_text = f"{latest_threh}W"
        
        figlmp=go.Figure()
        figconsumption = go.Figure()   
        figpriority =go.Figure()
        bar_fig1 = go.Figure()  
        
    # define the charts
        figlmp.add_trace(go.Scatter(x=df_total_consumption['timestamp'], y=lmptrend,
                    line=dict(color='red', width=2),
                    name='lmptrend'))

        figconsumption.add_trace(go.Scatter(x=df_total_consumption['timestamp'], y=df_total_consumption['power'],
                    line=dict(color='blue', width=2),
                    name='Power consumption'))
        figconsumption.add_trace(go.Scatter(x=df_total_consumption['timestamp'], y=df_total_consumption['Threshold'],
                    line=dict(color='firebrick', width=2,
                              dash='dash'),
                    name='Threshold'))   
        bar_fig1.add_trace(go.Bar(x=['Wind '],y=[0],name='latestwind', text=f'{0} W',textfont=dict(color='black',weight='bold',size=16)),)
        bar_fig1.add_trace(go.Bar(x=['Total load '],y=[latest_power],name='Total sum',text=f'{latest_power} W',textfont=dict(color='black',weight='bold',size=16),))

        for priority in df_priority_grouped['priority'].unique()[::-1]:
            priority_data = df_priority_grouped[df_priority_grouped['priority'] == priority]
            try:
                figpriority.add_trace(go.Scatter(x=priority_data['timestamp'], y=priority_thresholds_list[str(priority)],
                        line=dict( width=2,dash='dash'),
                        name=f'Group {priority} Threshold'))
            except:
                pass
            figpriority.add_trace(go.Scatter(x=priority_data['timestamp'], y=priority_data['power'],
                        line=dict( width=2),
                        name=f'Group {priority}'))
            try:
                bar_fig1.add_trace(go.Bar(x=['Groups Consumption'],y=[priority_data[priority_data['timestamp'] == latest_time]['power'].values[0]],name=f'Group {priority}',text=str(round(priority_data[priority_data['timestamp'] == latest_time]['power'].values[0]))+' W',textfont=dict(color='black',weight='bold',size=16),))

            except:
                pass
                        
              
        bar_fig1.update_layout(
        barmode='stack',  # Stack the bars for priority groups
        showlegend=True,
        xaxis=dict(
            title='DER',
            tickfont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=18,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            ),
            titlefont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=20,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            ),

        ),
        yaxis=dict(
            title='Power (W)',
            tickfont=dict(
                family="Courier New",  # Font family for Y-axis ticks
                size=18,               # Font size for Y-axis ticks
                color="black",          # Font color for Y-axis ticks
                weight= 'bold'
            ),
            titlefont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=20,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            ),
            range=[0, max([0 if latest_threh == None else latest_threh,latest_power]) + 5000],
            
        ),
        
        shapes=[  # Add a horizontal line to represent the threshold
            dict(
                type="line",
                x0=-0.5,  # Start the line before the first bar (slightly to the left)
                x1=2.5,  # End the line after the second bar (slightly to the right)
                y0=0 if latest_threh == None else latest_threh,  # The y-coordinate for the threshold line (the same for both x0 and x1)
                y1=0 if latest_threh == None else latest_threh,  # The y-coordinate for the threshold line
                line=dict(color="red", width=3, dash="dash"),  # Customize the color, width, and dash style
            )
        ], 
        annotations=[  # Add text near the threshold line
            dict(
                x=1,  # Positioning on the x-axis
                y=0 if latest_threh == None else latest_threh +250,  # Positioning on the y-axis (same as the threshold line)
                xref="x",  # Reference to x-axis
                yref="y",  # Reference to y-axis
                text=f"Consumption Threshold: {latest_threh} W",  # The text to display
                showarrow=False,  # No arrow for the annotation
                font=dict(
                    size=12,  # Font size for the annotation
                    color="black"  # Color for the annotation text
                ),
                align="center",  # Center alignment for the text
                ax=0,  # No offset on the x-axis
                ay=-10,  # Small offset on the y-axis to place the text above the line
            )
        ],
    )            
        figpriority.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='white',
            plot_bgcolor='#d9e0ea',
            hovermode='x unified',
            xaxis_title="Time(HH:mm)",
            yaxis_title="Consumption (W)",
            legend=dict(
            orientation="h",  # Set the legend to be horizontal
            yanchor="bottom",  # Anchor the legend to the bottom
            y=-0.2,  # Place the legend below the plot (adjust as necessary)
            xanchor="center",  # Center the legend horizontally
            x=0.5  # Center the legend on the x-axis
        ),
            xaxis=dict(
            tickfont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=18,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            ),
            titlefont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=18,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            )
        ),
            yaxis=dict(
            tickfont=dict(
                family="Courier New",  # Font family for Y-axis ticks
                size=18,               # Font size for Y-axis ticks
                color="black",          # Font color for Y-axis ticks
                weight= 'bold'
            ),
            titlefont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=18,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            )
        )   
            
        )
        
        # Add the latest value as an annotation
        figconsumption.add_annotation(
            x=df_total_consumption['timestamp'].iloc[-1],  # X coordinate for the text
            y=latest_threh,  # Y coordinate for the text
            text=latest_value_text,  # Text to display
            showarrow=True,  # Arrow pointing to the point
            arrowhead=2,  # Arrow style
            ax=0,  # X offset for the text
            ay=-100,  # Y offset for the text
            font=dict(size=16, color="red", weight='bold'),  # Font styling for the text
            #bgcolor="white",  # Background color for the text box
            #bordercolor="black",  # Border color for the text box
        )
        
        figconsumption.add_annotation(
            x=df_total_consumption['timestamp'].iloc[-1],  # X coordinate for the text
            y=df_total_consumption['power'].iloc[-1],  # Y coordinate for the text
            text=f'{latest_power}W',  # Text to display
            showarrow=True,  # Arrow pointing to the point
            arrowhead=2,  # Arrow style
            ax=0,  # X offset for the text
            ay=-50,  # Y offset for the text
            font=dict(size=16, color="blue", weight='bold'),  # Font styling for the text
            #bgcolor="white",  # Background color for the text box
            #bordercolor="black",  # Border color for the text box
        )
        figconsumption.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='white',
            plot_bgcolor='#d9e0ea',
            hovermode='x unified',
            xaxis_title="Time(HH:mm)",
            yaxis_title="Consumption (W)",
            legend=dict(
            orientation="h",  # Set the legend to be horizontal
            yanchor="bottom",  # Anchor the legend to the bottom
            y=-0.2,  # Place the legend below the plot (adjust as necessary)
            xanchor="center",  # Center the legend horizontally
            x=0.5  # Center the legend on the x-axis
        ),
            xaxis=dict(
            tickfont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=18,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            ),
            titlefont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=18,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            )
        ),
            yaxis=dict(
            tickfont=dict(
                family="Courier New",  # Font family for Y-axis ticks
                size=18,               # Font size for Y-axis ticks
                color="black",          # Font color for Y-axis ticks
                weight= 'bold'
            ),
            titlefont=dict(
                family="Courier New",  # Font family for X-axis ticks
                size=18,               # Font size for X-axis ticks
                color="black",          # Font color for X-axis ticks
                weight= 'bold'
            )
        )   
            
        )
        
        figconsumption.update_xaxes(
        showgrid=True,   # Show x-axis grid lines
        gridwidth=1,     # Width of x-axis grid lines
        gridcolor='#cccccc'  # Color of x-axis grid lines
        )
        figconsumption.update_yaxes(
            showgrid=True,   # Show y-axis grid lines
            gridwidth=1,     # Width of y-axis grid lines
            gridcolor='#cccccc'  # Color of y-axis grid lines
        )
                     
        return figconsumption,figlmp,figpriority, bar_fig1