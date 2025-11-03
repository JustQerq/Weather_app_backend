from flask import Flask, render_template, request
import sqlite3
from requests_manager import WeatherRequestsManager


app = Flask(__name__)
weather_req_manager = WeatherRequestsManager()

@app.route('/')
@app.route('/home')
def index():
    return render_template('index_html')

@app.route('/weather/history', methods=['GET'])
def get_weather():
    conditions_received = []
    
    # Field values to filter (e.g. WHERE field = value)
    fields = ["rowid", "datetime", "city", "country", "temperature", \
            "temperature_feels", "humidity", "condition"]
    fields_received = []
    for field in fields:
        value = request.args.get(field, None)
        if value is not None:
            conditions_received.append(f"{field}={value}")
    
    # Greater conditionals (e.g. WHERE field > value)
    greater = ["rowid_gr", "datetime_gr", "temperature_gr", "temperature_feels_gr", "humidity_gr"]
    for gr in greater:
        value = request.args.get(gr, None)
        if value is not None:
            conditions_received.append(f"{field}={value}")
            
    # Less conditionals (e.g. WHERE field < value)
    less = ["rowid_ls", "datetime_ls", "temperature_ls", "temperature_feels_ls", "humidity_ls"]
    for ls in less:
        value = request.args.get(ls, None)
        if value is not None:
            conditions_received.append(f"{field}={value}")
    
    sql_condition = ""
    if len(conditions_received) > 0:
        sql_condition = " WHERE" + " AND ".join(conditions_received)
             
    
    with sqlite3.connect('weather.db') as con:
        cur = con.cursor()
        cur.execute('SELECT * FROM weather_data' + sql_condition)
        data = cur.fetchall()
        
        # no entries found in the database, need to send a request to weather API
        if len(data) == 0:
            if "datetime" in conditions_received:
                data_json = weather_req_manager.get("history", dt=request.args.get("datetime"))
            elif "datetime_gr":
                data_json = weather_req_manager.get("history", dt=request.args.get("datetime_gr"))
            elif "datetime_ls":
                data_json = weather_req_manager.get("history", dt=request.args.get("datetime_ls"))

            # Transform the received dict into a list of database fields
    
    return render_template('weather.html', data=data)