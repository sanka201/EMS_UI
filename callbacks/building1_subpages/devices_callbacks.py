# callbacks/building1_subpages/devices_callbacks.py

from dash import Input, Output, State, html
from app_instance import app
from db_connection import get_connection
import json
from pandas import json_normalize
import pandas as pd
from UserInterface.components.devicetable import DeviceTable
import plotly.graph_objects as go
# Example callback for updating devices content
@app.callback(
    Output('gnire-building-540-data-store', 'data'),
    Input('nire-building-540-update-interval', 'n_intervals')
)
def update_devices_content(n):
    data={
        'data': n
    }
    # Implement logic to update devices information
    return data


def make_data_list(data_list):
    load_data_list = []
    for row in data_list:
        ts, value_string = row
        tempdata = json.loads(value_string)
        load_data_list.append((ts, tempdata))
    return load_data_list

@app.callback(
    Output('devices-figure','figure'),
        Output('device-table','figure'),
    Input('nire-building-540-update-interval', 'n_intervals')
)
def query_database(n):
    # Fetch data from the database
    load_conn = None
    load_cursor = None
    meter_conn = None
    meter_cursor = None
    table =None
    try:
        load_conn,meter_conn = get_connection()
        load_cursor = load_conn.cursor()
        meter_cursor = meter_conn.cursor()

        # Query to get all necessary data
        load_query =""" SELECT ts, value_string FROM GLEAMM_NIRE.data  where topic_id=5 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 3 hour) ORDER BY ts DESC """
        meter_query =""" SELECT ts, value_string FROM GLEAMM_NIRE_meters.data  where topic_id=1 and  ts <= UTC_TIMESTAMP()   and ts >=date_sub( UTC_TIMESTAMP() , interval 5 hour) ORDER BY ts DESC """
        load_cursor.execute(load_query)
        meter_cursor.execute(meter_query)
        load_result = load_cursor.fetchall()
        meter_result = meter_cursor.fetchall()
        #load data in to a tuple
        load_data_list= make_data_list(load_result)
        meter_data_list =make_data_list(meter_result)
        dfloads = pd.concat([json_normalize(data.get('Monitor', {}).get('building540',{}), sep='@').assign(timestamp=timestamp) for timestamp, data in load_data_list], ignore_index=True)
        #plugdata=load_data_list[1].get('Monitor', {}).get('building540',{})
        filtered_columns_power = [col for col in dfloads.columns if ('@power') in col.lower()]
        filtered_columns_maxpower = [col for col in dfloads.columns if ('@maxpower') in col.lower()]
        filtered_columns_status = [col for col in dfloads.columns if ('@status') in col.lower()]
        filtered_columns_priority = [col for col in dfloads.columns if ('@priority') in col.lower()]
        status_val =[]
        for status in dfloads[filtered_columns_status].iloc[0]:
            if status == 1:
                status_val.append('🟢 On')
            elif status == 0:
                status_val.append('🔴 Off')       
            elif status == 8:
                status_val.append('🟡  Standby')                 
            elif status ==2:
                status_val.append('✅ connected')
            else:
                status_val.append('❌ Comm Error')                    
                
        load_tags = [ col.split('@')[-2] for col in filtered_columns_power ]
        # prepare data for the table component
        df = pd.DataFrame({
            'Device ID': load_tags,
            'Power Usage (W)': list(dfloads[filtered_columns_power].iloc[0].round(1)),
            'Power Max (W)': list(dfloads[filtered_columns_maxpower].iloc[0].round(1)),
            'Status': status_val,
            'Priority': list(dfloads[filtered_columns_priority].iloc[0])
            
                            })
        
        figdevices=go.Figure()
        for device in list(dfloads[filtered_columns_power]):
            figdevices.add_trace(go.Scatter(x=dfloads['timestamp'], y=list(dfloads[device]),
                    line=dict( width=2),
                    name=device))
        table =DeviceTable(df)


    
    except:
        pass
    return figdevices, table