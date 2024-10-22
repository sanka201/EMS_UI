# callbacks/building1_callbacks.py

from dash import Input, Output, State, html
from app_instance import app
import random
import pandas as pd
import plotly.express as px
import mysql.connector
import json
from db_connection import get_connection
import mysql.connector
from datetime import datetime,timedelta
import plotly.graph_objects as go
from pandas import json_normalize
from dash import Input, Output, State, html
from app_instance import app
from plotly.subplots import make_subplots

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
    for priority in priority_thresholds:
        priority_thresholds[priority].reverse()
    total_thresholds.reverse()
    return priority_thresholds, total_thresholds


# Callback to query data and store it in dcc.Store
@app.callback(
    Output('building1-data-store', 'data'),
    Input('building1-update-interval', 'n_intervals')
)
def query_database(n_intervals):
    # Fetch data from the database
    conn = None
    cursor = None
    try:
        conn,conn2 = get_connection()
        cursor = conn.cursor()
        cursor2 = conn2.cursor()
        # Query to get all necessary data
        query =""" SELECT ts, value_string FROM GLEAMM_NIRE.data  where topic_id=5 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 3 hour) ORDER BY ts DESC """
        query2 =""" SELECT ts, value_string FROM GLEAMM_NIRE_meters.data  where topic_id=1 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 3 hour) ORDER BY ts DESC """
        query3 =""" SELECT ts, value_string FROM GLEAMM_NIRE.data  where topic_id=9 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 3 hour) ORDER BY ts DESC """
        
        cursor.execute(query)
        cursor2.execute(query2)
        result = cursor.fetchall()
        result2 = cursor2.fetchall()
        #result3 = cursor3.fetchall()
        data_list = []
        for row in result:
            ts, value_string = row
            tempdata = json.loads(value_string)
            data_list.append((ts, tempdata))
            
        data_list2 = []    
        for row in result2:
            ts, value_string = row
            tempdata = json.loads(value_string)
            data_list2.append((ts, tempdata))
        cursor.execute(query3)
        result = cursor.fetchall()            
        data_list3 = []    
        for row in result:
             ts, value_string = row
             tempdata = json.loads(value_string)
             data_list3.append((ts, tempdata))
                        
            
        # Extract control commands and guess missing thresholds
        control_commands = [data.get('Control', {}).get('Django', {}).get('cmd', None) for _, data in data_list]
# Flatten the JSON for each (timestamp, data) pair and add the timestamp as a column        
        storage = [{'ts':ts, "batt1":data.get('storage', {}).get('battery1', None),"batt2":data.get('storage', {}).get('battery2', None)} for ts, data in data_list3]

       
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
            
        priority_thresholds_list, total_thresholds_list=guess_missing_thresholds_spit(control_commands)
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
            # Handle EV data
            for ev_device, metrics in data.get('Monitor', {}).get('EV', {}).items():
                priority_trend_list.append({
                    'timestamp': ts,
                    'priority': metrics.get('priority'),
                        'power' : round(metrics.get('power'),1)
                })
        tempdata=latest_data[1].get('Monitor', {}).get('building540',{}).get('EV',{}).get('building540/EV/JuiceBox')
        Evpower=tempdata.get('power')
        Evenergy=tempdata.get('energy')
        Evstatus=tempdata.get('status')
        Evtemerature=tempdata.get('temperature')
        Evcurrent=tempdata.get('current')
        Evvoltage=tempdata.get('voltage')
        Evfrequency=tempdata.get('frequency')
        print()      
        #df_priority_trend = pd.DataFrame(priority_trend_list) 
        #df_priority_grouped = df_priority_trend.groupby(['timestamp', 'priority']).sum().reset_index()       
        data = {
            'LMP':round(LMP/1000,3),
            'LMPhr': round(sum(filtered_tuples)/1000/len(filtered_tuples),3),
            'Evstatus': Evstatus,
            'EvPower': round(Evpower/1000,3),
            'Evenergy': Evenergy,
            'prioritytrend': priority_trend_list,
            'thresholdlist': total_thresholds_list,
            'prioritythresholdlist':priority_thresholds_list,
            'meters':data_list2,
            'lmptrend':lmptrend[::-1],
            'storage': storage
            }
        # if result:
        #     # Process the data as needed
        #     data = {
        #         'ev_status': result['status'],
        #         'battery_level': result['battery_level'],
        #         'ev_timestamp': result['timestamp'],
        #         'consumption_timestamp': result['consumption_timestamp'],
        #         'consumption': result['consumption']
        #     }
        # else:
        #     # Default values if no data is found
        #     data = {
        #         'ev_status': 'Disconnected',
        #         'battery_level': 0,
        #         'ev_timestamp': None,
        #         'consumption_timestamp': None,
        #         'consumption': 0
        #     }
        


    except mysql.connector.Error as err:
        print(f"Error: {err}")
        # Return default data in case of error
        return {
            'ev_status': 'Disconnected',
            'battery_level': 0,
            'ev_timestamp': None,
            'consumption_timestamp': None,
            'consumption': 0
        }
    finally:
        
        cursor.close()
        conn.close()
    return data

# Define EV statuses and their corresponding icons and colors
EV_STATUSES = {
    'Charging': {
        'icon_class': 'fas fa-bolt',
        'color': '#28a745'  # Green
    },
    'Connected': {
        'icon_class': 'fas fa-plug',
        'color': '#007bff'  # Blue
    },
    'Disconnected': {
        'icon_class': 'fas fa-times-circle',
        'color': '#dc3545'  # Red
    }
}



# Callback to update real-time marginal price
@app.callback(
    [Output('building1-realtime-marginal-price', 'children'),
     Output('building1-realtime-marginal-trend', 'children'),
     Output('building1-hourly-price', 'children'),
     Output('building1-hourly-price-trend', 'children')],
    [Input('building1-data-store', 'data')]
)
def update_realtime_marginal_price(data):
    # Simulate price data
    price=data.get('LMP', 0)
    trend_icon = html.I(className='fas fa-arrow-up', style={'color': 'green'}) if random.choice([True, False]) else html.I(className='fas fa-arrow-down', style={'color': 'red'})
    hrprice=data.get('LMPhr', 0)
    hrtrend_icon = html.I(className='fas fa-arrow-up', style={'color': 'green'}) if random.choice([True, False]) else html.I(className='fas fa-arrow-down', style={'color': 'red'})

    
    return f"${price}/kWh", trend_icon,f"${hrprice}/kWh", hrtrend_icon

# Repeat similar callbacks for 'building1-hourly-price' and 'building1-hourly-cost'

@app.callback(
    [Output('consumption-time-chart', 'figure'),
     Output('production-consumption-chart', 'figure'),
     Output('generation-time-chart', 'figure'),
     Output('lmp-time-chart', 'figure'),
     Output('building1-consumption-bar', 'figure'), Output('battery-SOC','figure')],
    Input('building1-data-store', 'data')
)
def update_consumption_time_chart(data):
    # Retrieve actual data for energy consumption over time
    # Replace the following with your data retrieval logic
    trend=pd.DataFrame( data['prioritytrend'])
    storage=pd.DataFrame( data['storage'])
    dfmeters = pd.concat([
    json_normalize(data, sep='_').assign(timestamp=timestamp) for timestamp, data in data['meters']
], ignore_index=True)
    dfmeters_latest=dfmeters.iloc[1]
    try :
        dfstorage = storage.iloc[1]
        battery_SOC=dfmeters_latest['storage_Battery_SOC']
        battery_voltage=dfmeters_latest['storage_Battery_Battery_voltage']/10
        battery_inv_load=dfmeters_latest['storage_Battery_INV1_Load_kW']+dfmeters_latest['storage_Battery_INV2_Load_kW']+dfmeters_latest['storage_Battery_INV3_Load_kW']
        battery_inv_buy=dfmeters_latest['storage_Battery_INV1_Buy_kW']+dfmeters_latest['storage_Battery_INV2_Buy_kW']+dfmeters_latest['storage_Battery_INV3_Buy_kW']
        battery_inv_sell=dfmeters_latest['storage_Battery_INV1_Sell_kW']+dfmeters_latest['storage_Battery_INV2_Sell_kW']+dfmeters_latest['storage_Battery_INV3_Sell_kW']
        battery_cc_watt=round((dfmeters_latest['storage_Battery_CC1_watt']+dfmeters_latest['storage_Battery_CC2_watt']+dfmeters_latest['storage_Battery_CC3_watt'])/1000,1)
        battery_inv_output=dfmeters_latest['storage_Battery_INV1_Output_kW']+dfmeters_latest['storage_Battery_INV2_Output_kW']+dfmeters_latest['storage_Battery_INV3_Output_kW']
        battery_charging_current = (dfmeters_latest['storage_Battery_CC1_battery_current']+dfmeters_latest['storage_Battery_CC2_battery_current']+dfmeters_latest['storage_Battery_CC3_battery_current'])/10 
        battery_status_table =  go.Figure(data=[go.Table(
    header = dict(
        values = [['<b>Inv Buy</b>'],['<b>Inv Sell</b>'],['<b>Inv load</b>'],['<b>Inv Out</b>'],['<b>Solar Input</b>'],['<b>Batt SOC</b>'],['<b>Batt Charging Amp</b>'],['<b>Batt Volt</b>']],
        line_color='darkslategray',
        fill_color='royalblue',
        align=['center','center'],
        font=dict(color='white', size=16),
    ),
    cells=dict(
        values=[str(battery_inv_buy)+' kW',str(battery_inv_sell)+' kW',str(battery_inv_load)+' kW',str(battery_inv_output)+' kW',str(battery_cc_watt)+' kW',str(battery_SOC)+' %',str(battery_charging_current)+' A',str(battery_voltage)+' V'],
        line_color='darkslategray',
        fill=dict(color=['paleturquoise', 'white']),
        fill_color='white',
        align=['center', 'center'],
        font=dict(family="Courier New",color='black', size=16,weight='bold'),
        height=40,)
        )
    ])

        battery_status_table.update_layout(
        autosize=True,
        height=130,
        margin=dict(l=5, r=5, t=5, b=0),  # Remove extra margins
)
    except:
        pass
            #html.P(id='building1-battery-SOC', className='card-text'),
            # html.P(id='building1-battery-voltage', className='card-text'),
            # html.P(id='building1-battery-AC-drop', className='card-text'),
            # html.P(id='building1-battery-inv-load', className='card-text'),
            # html.P(id='building1-battery-inv-buy', className='card-text'),
            # html.P(id='building1-battery-inv-sell', className='card-text'),
            # html.P(id='building1-battery-cc-watt', className='card-text'),
    
    
    lmptrend = data['lmptrend']
    threshold=data['thresholdlist']
    prioritythreshold=data['prioritythresholdlist']
    df_priority_grouped = trend.groupby(['timestamp', 'priority']).sum().reset_index()
    df_total_consumption = df_priority_grouped.groupby('timestamp').sum().reset_index()
    consumption_time_data = pd.DataFrame({
        'Timestamp': pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(hours=23), periods=24, freq='H'),
        'Consumption': [random.uniform(50, 150) for _ in range(24)]
    })
   
    df_total_consumption['Threshold']=threshold
    


    latest_threh= threshold[-1]
    latest_power= round(df_total_consumption['power'].iloc[-1])
    latest_time=df_total_consumption['timestamp'].iloc[-1]
    latest_value_text = f"{latest_threh}W"
    figpriority =go.Figure()
    fig = go.Figure()
    figgeneration=make_subplots(specs=[[{"secondary_y": True}]])#go.Figure()
    figlmp=go.Figure()
    figbatt =  go.Figure()
    latestwind=pd.to_numeric(dfmeters['wind_Bergey_inverter_output_power'].iloc[1])
    
    
    
    

    
# define the charts
    figbatt.add_trace(go.Scatter(x=storage['ts'], y=storage['batt1'],
                    line=dict(color='red', width=2),
                    name='Battery1 SOC'))
    figbatt.add_trace(go.Scatter(x=storage['ts'], y=storage['batt2'],
                    line=dict(color='blue', width=2),
                    name='Battery2 SOC'))
    figlmp.add_trace(go.Scatter(x=df_total_consumption['timestamp'], y=lmptrend,
                    line=dict(color='red', width=2),
                    name='lmptrend'))
    figgeneration.add_trace(go.Scatter(x=dfmeters['timestamp'], y= pd.to_numeric(dfmeters['wind_Bergey_inverter_output_power']),
                    line=dict(color='#36802d', width=2),
                    name='Bergey'),secondary_y=False)
    figgeneration.add_trace(go.Scatter(x=dfmeters['timestamp'], y= lmptrend[::-1],
                    line=dict(color='red', width=2),
                    name='LMP price ($)'),secondary_y=True)
    fig.add_trace(go.Scatter(x=df_total_consumption['timestamp'], y=df_total_consumption['power'],
                    line=dict(color='blue', width=2),
                    name='Power consumption'))
    fig.add_trace(go.Scatter(x=df_total_consumption['timestamp'], y=df_total_consumption['Threshold'],
                    line=dict(color='firebrick', width=2,
                              dash='dash'),
                    name='Threshold'))
    color_map = ['red', 'green', 'blue', 'orange', 'purple']  # Example colors for different thresholds
    color_idx = 0
   # barchardata={'items':['Wind power','Total Controllable'],'power':[latestwind,latest_power]}
    
    #bar_fig_y_max= latestwind if latestwind> latest_power else latest_power
    bar_fig1 = go.Figure()  
    bar_fig1.add_trace(go.Bar(x=['Wind '],y=[latestwind],name='latestwind', text=f'{latestwind} W',textfont=dict(color='black',weight='bold',size=16)),)
    bar_fig1.add_trace(go.Bar(x=['Total load '],y=[latest_power],name='Total sum',text=f'{latest_power} W',textfont=dict(color='black',weight='bold',size=16),))
    bar_soc = go.Figure() 

    bar_soc.add_trace(go.Bar(x=['battery 1 '],y=[dfstorage['batt1']],name='battery 1 SOC', text=str(round(dfstorage['batt1'],2)) +'%',textfont=dict(color='black',weight='bold',size=16)),)
    bar_soc.add_trace(go.Bar(x=['battery 2  '],y=[dfstorage['batt2']],name='battery 2 SOC',text=str(round(dfstorage['batt2'],2))+ '%',textfont=dict(color='black',weight='bold',size=16),))
    
    
    
    for priority in df_priority_grouped['priority'].unique()[::-1]:
        priority_data = df_priority_grouped[df_priority_grouped['priority'] == priority]
        figpriority.add_trace(go.Scatter(x=priority_data['timestamp'], y=priority_data['power'],
                    line=dict( width=2),
                    name=f'Group {priority}'))
        try:
            figpriority.add_trace(go.Scatter(x=priority_data['timestamp'], y=prioritythreshold[str(priority)],
                    line=dict( width=2, dash='dash'),
                    name=f'Group {priority}'))
        except:
            pass
        # barchardata['items'].append(f'Group {priority}')
        # barchardata['power'].append(round(priority_data['power'].iloc[-1]))
        try:
            bar_fig1.add_trace(go.Bar(x=['Groups Consumption'],y=[priority_data[priority_data['timestamp'] == latest_time]['power'].values[0]],name=f'Group {priority}',text=str(round(priority_data[priority_data['timestamp'] == latest_time]['power'].values[0]))+' W',textfont=dict(color='black',weight='bold',size=16),))

        except:
            pass
        color_idx += 1     
        
        
    bar_soc.update_layout(
        height=300,
    barmode='stack',  # Stack the bars for priority groups
    showlegend=True,
    xaxis=dict(
        title='Battery SOC',
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
        title='SOC (%)',
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
        
    ),)   
        
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
         range=[0, max([0 if latest_threh == None else latest_threh,latestwind,latest_power]) + 500],
        
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

    figgeneration.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='#d9e0ea',
 hovermode='x unified',
    title={
        'text': "Power Generation (W) - GroupNIRE",  # Title text
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
    
    figgeneration.update_yaxes(
    title_text="LMP Pricing ($/unit)",
    title_font=dict(
        family="Courier New",
        size=18,
        color="red",
        weight= 'bold'
    ),
    tickfont=dict(
        family="Courier New",
        size=18,
        color="red",
        weight= 'bold'
    ),
    secondary_y=True  # Specifies the secondary y-axis
)

    
    figbatt.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='#d9e0ea',
        hovermode='x unified',
        xaxis_title="Time(HH:mm)",
        yaxis_title="Battery SOC (%)",
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
    
    
    figlmp.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='#d9e0ea',
        hovermode='x unified',
        xaxis_title="Time(HH:mm)",
        yaxis_title="Electricity price ($/kWh)",
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
    
    figpriority.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
                    hovermode='x unified',
    title={
        'text': "Individual Group Power Consumption (W) - GroupNIRE",  # Title text
        'x': 0.5,  # Center the title (x: 0 is left, 1 is right, 0.5 is center)
        'xanchor': 'center',  # Ensure the title is anchored in the center
        'yanchor': 'top',  # Anchor to the top
         'font': {'family':"Courier New",'size':24, 'weight': 'bold'}
    },
        paper_bgcolor='white',
        plot_bgcolor='#d9e0ea',
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
    fig.add_annotation(
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
    
    fig.add_annotation(
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
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='#d9e0ea',
                    hovermode='x unified',
    title={
        'text': "Total Contollable Load Power Consumption (W) - GroupNIRE",  # Title text
        'x': 0.5,  # Center the title (x: 0 is left, 1 is right, 0.5 is center)
        'xanchor': 'center',  # Ensure the title is anchored in the center
        'yanchor': 'top',  # Anchor to the top
         'font': {'family':"Courier New",'size':24, 'weight': 'bold'}
    },
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
    
    fig.update_xaxes(
    showgrid=True,   # Show x-axis grid lines
    gridwidth=1,     # Width of x-axis grid lines
    gridcolor='#cccccc'  # Color of x-axis grid lines
     )
    fig.update_yaxes(
        showgrid=True,   # Show y-axis grid lines
        gridwidth=1,     # Width of y-axis grid lines
        gridcolor='#cccccc'  # Color of y-axis grid lines
    )

   # return [fig,figpriority,figgeneration,figlmp,battery_status_table,bar_fig1,'Battery1: '+str(round(dfstorage['batt1'],1))+'%','Battery2: '+str(round(dfstorage['batt2'],1))+'%']
    return [fig,figpriority,figgeneration,figbatt,bar_fig1,bar_soc]
# @app.callback(
#     Output('production-consumption-chart', 'figure'),
#     Input('building1-update-interval', 'n_intervals')
# )
# def update_production_consumption_chart(n):
#     # Retrieve actual data for energy production vs. consumption
#     # Replace the following with your data retrieval logic
    
#     production_consumption_data = pd.DataFrame({
#         'Type': ['Production', 'Consumption'],
#         'Energy': [random.uniform(1000, 1500), random.uniform(1200, 1700)]
#     })

#     # Create the bar chart
#     production_consumption_fig = px.bar(
#         production_consumption_data,
#         x='Type',
#         y='Energy',
#         color='Type',
#         title='Energy Production vs. Consumption',
#         labels={'Energy': 'Energy (kWh)'},
#         color_discrete_map={'Production': '#1f77b4', 'Consumption': '#ff7f0e'}
#     )

#     production_consumption_fig.update_layout(
#         margin=dict(l=20, r=20, t=50, b=20),
#         paper_bgcolor='white',
#         plot_bgcolor='white',
#         showlegend=False
#     )

#     return production_consumption_fig


# callbacks/building1_callbacks.py

@app.callback(
    [Output('building1-ev-status', 'children'),
     Output('ev-status-icon', 'className'),
     Output('ev-status-icon', 'style'),
     Output('building1-ev-battery-level', 'children')],
    Input('building1-data-store', 'data')
)
def update_ev_info(data):
    # Simulate EV data
    Evstatus=data.get('Evstatus', 0)
    EvPower= data.get('EvPower',0)
    if Evstatus ==0:
        ev_status_display='Disconnected'
    elif Evstatus ==1:
        ev_status_display='Connected'
    else:
        ev_status_display='Charging'
    status = random.choice(list(EV_STATUSES.keys()))
    evpower = EvPower
    
    # Get the icon class and color based on the status
    status_info = EV_STATUSES[ev_status_display]
    icon_class = status_info['icon_class']
    color = status_info['color']
    
    # Styles for the status text and icon
    text_style = {'color': color}
    icon_style = {'color': color, 'font-size': '1.5em'}
    
    # Return the updated values
    return (f"EV Status: {ev_status_display}",
            icon_class,
            icon_style,
            f"Power output: {evpower} kW")
    

@app.callback(
    Output('building1-consumption-pie-chart', 'figure'),
    [Input('building1-update-interval', 'n_intervals')]
)
def update_consumption_pie_chart(n):
    # Simulate new consumption data
    consumption_data = {
        'Load Group': ['Lighting', 'HVAC', 'Equipment'],
        'Consumption': [
            random.randint(30, 50),
            random.randint(25, 45),
            random.randint(20, 40)
        ]
    }
    consumption_df = pd.DataFrame(consumption_data)
    consumption_df['Consumption'] = consumption_df['Consumption'] / consumption_df['Consumption'].sum() * 100  # Normalize to percentages

    # Create the pie chart
    consumption_pie_fig = px.pie(
        consumption_df,
        names='Load Group',
        values='Consumption',
        color='Load Group',
        color_discrete_map={
            'Lighting': '#1f77b4',
            'HVAC': '#ff7f0e',
            'Equipment': '#2ca02c'
        },
        hole=0.4  # For a donut chart effect
    )

    consumption_pie_fig.update_layout(
        showlegend=True,
        legend_title_text='Load Groups',
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return consumption_pie_fig
