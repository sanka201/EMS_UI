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
            total_thresholds.append(sum(cmd[1] for cmd in command.values()))
        elif isinstance(command, list) and len(command) == 2:
            last_total_threshold = command[1]
            current_priority_thresholds = None
            total_thresholds.append(last_total_threshold)
        else:
            current_priority_thresholds = None
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
    return priority_thresholds, total_thresholds


@app.callback(
    Output('home-data-store', 'data'),
    Input('home-update-interval', 'n_intervals')
)

def query_database(n_intervals):
    # Fetch data from the database
    conn = None
    cursor = None
    try:
        conn,conn2 = get_connection()
        cursor = conn.cursor()

        # Query to get all necessary data
        query =""" SELECT ts, value_string FROM GLEAMM_NIRE.data  where topic_id=5 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 3 hour) ORDER BY ts DESC """
        query2 =""" SELECT ts, value_string FROM GLEAMM_NIRE.data  where topic_id=8 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 3 hour) ORDER BY ts DESC """

        cursor.execute(query)

        result = cursor.fetchall()

        data_list_nire = []
        for row in result:
            ts, value_string = row
            tempdata = json.loads(value_string)
            data_list_nire.append((ts, tempdata))
            
        cursor.execute(query2)

        result = cursor.fetchall()

        data_list_gleamm = []
        for row in result:
            ts, value_string = row
            tempdata = json.loads(value_string)
            data_list_gleamm.append((ts, tempdata))            
       
        # Extract control commands and guess missing thresholds
        control_commands = [data.get('Control', {}).get('All_Groups', {}).get('cmd', None) for _, data in data_list_gleamm]
# Flatten the JSON for each (timestamp, data) pair and add the timestamp as a column              
       
        LMP = data_list_nire[0][1]['LMP']
        one_hour_ago=data_list_nire[0][0]-timedelta(hours=1)
        filtered_tuples = [tup[1]['LMP'] for tup in data_list_nire if tup[0] >= one_hour_ago]
        LMP_average_for_last_hour=sum(filtered_tuples)/1000/len(filtered_tuples)
        lmptrend = [round(tup[1]['LMP']/1000,3) for tup in data_list_nire ]

            
        priority_thresholds_list, total_thresholds_list=guess_missing_thresholds_spit(control_commands)
        # Process data for total consumption and priority consumption
        priority_trend_list_nire = []
        data_index=0       
        for ts, data in data_list_nire:
            for monitor, buildings in data.get('Monitor', {}).items():
                for building, devices in buildings.items():
                    for device, metrics in devices.items():
                        try:
                            priority_trend_list_nire.append({
                                'timestamp': ts,
                                'priority': metrics.get('priority'),
                                'power': metrics.get('power'),
                                'priority_thresh':priority_thresholds_list[str(metrics.get('priority'))][data_index]  
                            })
                        except:
                                priority_trend_list_nire.append({
                                'timestamp': ts,
                                'priority': metrics.get('priority'),
                                'power': metrics.get('power'),
                                'priority_thresh':None
                            })
            
            data_index+=1               
        priority_trend_list_gleamm = []
        data_index=0
        for ts, data in data_list_gleamm:
            for monitor, buildings in data.get('Monitor', {}).items():
                for building, devices in buildings.items():
                    for device, metrics in devices.items():
                        try:
                            priority_trend_list_gleamm.append({
                                'timestamp': ts,
                                'priority': metrics.get('priority'),
                                'power': metrics.get('power'),
                                'threshold':total_thresholds_list[data_index],
                                'priority_thresh':priority_thresholds_list[str(metrics.get('priority'))][data_index]
                            })
                        except:
                            priority_trend_list_gleamm.append({
                                'timestamp': ts,
                                'priority': metrics.get('priority'),
                                'power': metrics.get('power'),
                                'threshold':total_thresholds_list[data_index],
                                'priority_thresh':None
                            })                            
  
            data_index+=1     
        data = {
            'dbconnectivity' : 'online',
            'LMP':round(LMP/1000,3),
            'LMPhr': round(sum(filtered_tuples)/1000/len(filtered_tuples),3),
            'Evstatus': 'Not configured',
            'EvPower': None,
            'Evenergy': None,
            'prioritytrendnire': priority_trend_list_nire,
            'prioritytrendgleamm': priority_trend_list_gleamm,
            'thresholdlist': total_thresholds_list,
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



@app.callback(
    [Output('consumption-chart','figure'), Output('total-power-chart','figure'), Output('priority-power-chart','figure')],
         Input('home-data-store', 'data')
)
def update_consumption_time_chart(data):
    
        lmptrend = data['lmptrend']
        trendnire=pd.DataFrame( data['prioritytrendnire'])
        trendgleamm=pd.DataFrame( data['prioritytrendgleamm'])
        threshold=data['thresholdlist']
        trendnire_resample= pd.DataFrame( data['prioritytrendnire'])
        trendgleamm_resample= pd.DataFrame( data['prioritytrendgleamm'])
        trendnire_resample['timestamp'] = pd.to_datetime(trendnire_resample['timestamp'])
        trendgleamm_resample['timestamp'] = pd.to_datetime(trendgleamm_resample['timestamp'])
        trendnire_resample.set_index('timestamp', inplace=True)
        trendgleamm_resample.set_index('timestamp', inplace=True)
        total_power_resampled_nire = None
        total_power_resampled_gleamm = None
        # Define an empty dictionary to hold the resampled DataFrames for each priority level
        prioritypower=go.Figure()
        trendgleamm_resample_pr=trendgleamm_resample.groupby('priority')
        resampled_Th = trendgleamm_resample_pr.get_group(list(trendgleamm_resample_pr.groups.keys())[1])['threshold'].resample('40S').mean()
        
        bar_fig = go.Figure()
        temp=[]  
        # Group the data by 'priority' and resample the power for each group
        for priority, group in trendnire_resample.groupby('priority'):
            #print(priority)
            # Resample the data to 40-second intervals, summing the power
            resampled = group['power'].resample('40S').sum()
            resampled_pr_Th = group['priority_thresh'].resample('40S').sum()
            pd.set_option('display.max_rows', None)
            pd.reset_option('display.max_rows')

        # Add the resampled power to the total power Data
 
            if total_power_resampled_nire is None:
                total_power_resampled_nire = resampled.copy()
            else:
                total_power_resampled_nire = total_power_resampled_nire.add( resampled,fill_value=0)  # Sum the power for each priority level
            prioritypower.add_trace(go.Scatter(x= resampled.index, y= resampled ,
                     line=dict( width=2,),
                     name=f'Group {priority}'))
            prioritypower.add_trace(go.Scatter(x= resampled_pr_Th.index, y= resampled_pr_Th ,
                     line=dict( width=2,dash='dash'),
                     name=f'Group {priority}'))   
        # Group the data by 'priority' and resample the power for each group
        for priority, group in trendgleamm_resample_pr:
            #print(priority)
            # Resample the data to 40-second intervals, summing the power
            resampled = group['power'].resample('40S').sum()
            resampled_pr_Th = group['priority_thresh'].resample('40S').sum()
            prioritypower.add_trace(go.Scatter(x= resampled.index, y= resampled ,
                     line=dict( width=2,),
                     name=f'Group {priority}'))       
            prioritypower.add_trace(go.Scatter(x= resampled_pr_Th.index, y= resampled_pr_Th ,
                     line=dict( width=2,dash='dash'),
                     name=f'Group Threshold{priority}')) 
     
        # Add the resampled power to the total power DataFrame
            if total_power_resampled_gleamm is None:
                total_power_resampled_gleamm = resampled.copy()  # Initialize if empty
            else:
                total_power_resampled_gleamm = total_power_resampled_gleamm.add( resampled,fill_value=0)  # Sum the power for each priority level      
        total_power=total_power_resampled_gleamm.add(total_power_resampled_nire,fill_value=0)

        latest_threh= threshold[-1]
        latest_power_nire= total_power_resampled_nire.iloc[-1]# round(df_total_consumption_nire['power'].iloc[-1])
        latest_power_gleamm= total_power_resampled_gleamm.iloc[-1] #round(df_total_consumption_gleamm['power'].iloc[-1])
        latest_power_text = f"{round(latest_power_nire+latest_power_gleamm)} W"
        latest_value_text = f"{latest_threh}W"
        

        bar_fig.add_trace(go.Bar(x=['Total Consumption '],y=[latest_power_gleamm],name='GLEAMM',text=str(round(latest_power_gleamm))+' W',textfont=dict(color='black',weight='bold',size=16),))
        bar_fig.add_trace(go.Bar(x=['Total Consumption '],y=[latest_power_nire],name='NIRE',text=str(round(latest_power_nire))+' W',textfont=dict(color='black',weight='bold',size=16),))
        bar_fig.add_trace(go.Bar(x=['GLEAMM '],y=[latest_power_gleamm],name='GLEAMM',text=str(round(latest_power_gleamm))+' W', textfont=dict(color='black',weight='bold',size=16)),)
        bar_fig.add_trace(go.Bar(x=['NIRE '],y=[latest_power_nire],name='NIRE',text=str(round(latest_power_nire)),textfont=dict(color='black',weight='bold',size=16),))

        
        figlmp=go.Figure()

        
        totalconsumption = go.Figure()
        
        totalconsumption.add_trace(go.Scatter(x= total_power.index, y= total_power,
                     line=dict(color='blue', width=2),
                     name='Power consumption'))
        totalconsumption.add_trace(go.Scatter(x= resampled_Th.index, y= resampled_Th ,
                     line=dict(color='red', width=2, dash='dash'),
                     name='Threshold'))
        
        # Add the latest value as an annotation
        totalconsumption.add_annotation(
        x=resampled_Th.index[-1],  # X coordinate for the text
        y=resampled_Th.iloc[-1],  # Y coordinate for the text
        text=f'{round(resampled_Th.iloc[-1])} W',  # Text to display
        showarrow=True,  # Arrow pointing to the point
        arrowhead=2,  # Arrow style
        ax=0,  # X offset for the text
        ay=-100,  # Y offset for the text
        font=dict(size=16, color="red", weight='bold'),  # Font styling for the text
        #bgcolor="white",  # Background color for the text box
        #bordercolor="black",  # Border color for the text box
    )
    
        totalconsumption.add_annotation(
        x=total_power.index[-1],  # X coordinate for the text
        y=latest_power_nire+latest_power_gleamm,  # Y coordinate for the text
        text=f'{latest_power_text}W',  # Text to display
        showarrow=True,  # Arrow pointing to the point
        arrowhead=2,  # Arrow style
        ax=0,  # X offset for the text
        ay=-50,  # Y offset for the text
        font=dict(size=16, color="blue", weight='bold'),  # Font styling for the text
        #bgcolor="white",  # Background color for the text box
        #bordercolor="black",  # Border color for the text box
    )
        #place holder for the bar chart
        
        
        totalconsumption.update_layout(
                showlegend=True,
                        hovermode='x unified',
    title={
        'text': "Total Building Power Consumption (W)",  # Title text
        'x': 0.5,  # Center the title (x: 0 is left, 1 is right, 0.5 is center)
        'xanchor': 'center',  # Ensure the title is anchored in the center
        'yanchor': 'top',  # Anchor to the top
         'font': {'family':"Courier New",'size':24, 'weight': 'bold'}
    },
        xaxis_title="Time(HH:mm)",
        yaxis_title="Generation (W)",
        legend=dict(
        orientation="h",  # Set the legend to be horizontal
        yanchor="bottom",  # Anchor the legend to the bottom
        y=-0.2,  # Place the legend below the plot (adjust as necessary)
        xanchor="center",  # Center the legend horizontally
        x=0.5  # Center the legend on the x-axis
    ),
        xaxis=dict(
        title='Time',
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
        title='Power Consumption (W)',
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

        )
        
        prioritypower.update_layout(
                showlegend=True,
                        hovermode='x unified',
    title={
        'text': "Individual Group Power Consumption (W)",  # Title text
        'x': 0.5,  # Center the title (x: 0 is left, 1 is right, 0.5 is center)
        'xanchor': 'center',  # Ensure the title is anchored in the center
        'yanchor': 'top',  # Anchor to the top
         'font': {'family':"Courier New",'size':24, 'weight': 'bold'}
    },
        xaxis_title="Time(HH:mm)",
        yaxis_title="Generation (W)",
        legend=dict(
        orientation="h",  # Set the legend to be horizontal
        yanchor="bottom",  # Anchor the legend to the bottom
        y=-0.2,  # Place the legend below the plot (adjust as necessary)
        xanchor="center",  # Center the legend horizontally
        x=0.5  # Center the legend on the x-axis
    ),
        xaxis=dict(
        title='Time',
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
        title='Power Consumption (W)',
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

        )
        

        bar_fig.update_layout(
            barmode='stack',  # Stack the bars for priority groups
            showlegend=True,)
        bar_fig.update_layout(
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
         range=[0, max([0 if latest_threh == None else latest_threh,latest_power_gleamm+latest_power_nire]) + 500],
        
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
        return bar_fig,totalconsumption,prioritypower