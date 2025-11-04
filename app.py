from flask import Flask, render_template, request, jsonify
import sqlite3
from requests_manager import WeatherRequestsManager
from database_manager import params2sql, validate_weather
import json
import datetime


app = Flask(__name__)
weather_req_manager = WeatherRequestsManager()
weather_data_fields = ["rowid", "datetime", "city", "country", "latitude", "longitude", "temperature_c", \
        "feelslike_c", "humidity", "condition", "wind_kph"]



@app.route('/')
@app.route('/home')
def index():
    return render_template('index_html')


@app.route('/weather/current', methods=["GET"])
def get_weather_current():
    params = ["city", "country", "lat", "lon"]
    data_dict = None
    data = [[]]
    
    value_city = request.args.get("city", None)
    if value_city is not None:
        value_country = request.args.get("country", None)
        if value_country is not None:
            data_dict = weather_req_manager.get("current", q=f"{value_city}, {value_country}")
        else:
            data_dict = weather_req_manager.get("current", q=value_city)
    else:
        value_latitude = request.args.get("latitude", None)
        value_longitude = request.args.get("longitude", None)
        
        if (value_latitude is not None) and (value_longitude is not None):
            try:
                value_latitude = float(value_latitude)
                value_longitude = float(value_longitude)
                if ((value_latitude >= -90) and (value_latitude <= 90)) and ((value_longitude >= -180) and (value_longitude <= 180)):
                    data_dict = weather_req_manager.get("current", q=f"{value_latitude}, {value_longitude}")
            except:
                pass
    print(json.dumps(data_dict))
    
    data_returning = [[]]
    if (data_dict is not None) and (data_dict.get("error", None) is None):
        data[0].append(data_dict["current"]["last_updated"])
        data[0].append(data_dict["location"]["name"])
        data[0].append(data_dict["location"]["country"])
        data[0].append(data_dict["location"]["lat"])
        data[0].append(data_dict["location"]["lon"])
        data[0].append(data_dict["current"]["temp_c"])
        data[0].append(data_dict["current"]["feelslike_c"])
        data[0].append(data_dict["current"]["humidity"])
        data[0].append(data_dict["current"]["condition"]["text"])
        data[0].append(data_dict["current"]["wind_kph"])
        
        with sqlite3.connect('weather.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO weather_data \
                (datetime, city, country, latitude, longitude, temperature_c, \
                    feelslike_c, humidity, condition, wind_kph) \
                        VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING rowid, *", data[0])
            data_returning = cur.fetchall()  # Using the data from RETURNING clause to get the inserted row ids
            con.commit()
        
    
    return render_template('weather.html', data=data_returning)


@app.route('/weather/history/<int:rowid>', methods=['GET'])
def get_weather_history(rowid):
    with sqlite3.connect("weather.db") as con:
        cur = con.cursor()
        cur.execute("SELECT " + ", ".join(weather_data_fields) + " FROM weather_data WHERE rowid=" + str(rowid))
        data = cur.fetchall()
    return render_template("weather.html", data=data)


@app.route('/weather/history', methods=['GET'])
def get_weather_history_search():
    conditions = []
    
    # Equality conditionals (e.g. WHERE field = value)
    params_eq_dtypes = {"datetime": str, "city": str, "country": str, "latitude": float, "longitude": float, "temperature_c": float, \
            "feelslike_c": float, "humidity": float, "condition": str}
    conditions += params2sql(received_params=request.args, params_dtypes=params_eq_dtypes, relationship="=")
    
    # Greater conditionals (e.g. WHERE field > value)
    params_gr_dtypes = {"datetime_gr": str, "temperature_c_gr": float, "feelslike_c_gr": float, "humidity_gr": float}
    params_gr_aliases = {"datetime_gr": "datetime", "temperature_c_gr": "temperature_c", \
        "feelslike_c_gr": "feelslike_c", "humidity_gr": "humidity"}
    conditions += params2sql(received_params=request.args, params_dtypes=params_gr_dtypes, params_aliases=params_gr_aliases, relationship=">")
            
    # Less conditionals (e.g. WHERE field < value)
    params_ls_dtypes = {"datetime_ls": str, "temperature_c_ls": float, "feelslike_c_ls": float, "humidity_ls": float}
    params_ls_aliases = {"datetime_ls": "datetime", "temperature_c_ls": "temperature_c", \
        "feelslike_c_ls": "feelslike_c", "humidity_ls": "humidity"}
    conditions += params2sql(received_params=request.args, params_dtypes=params_ls_dtypes, params_aliases=params_ls_aliases, relationship="<")
    
    sql_condition = ""
    if len(conditions) > 0:
        sql_condition = " WHERE " + " AND ".join(conditions)   
    
    with sqlite3.connect('weather.db') as con:
        cur = con.cursor()
        cur.execute("SELECT " + ", ".join(weather_data_fields) + " FROM weather_data" + sql_condition)
        data = cur.fetchall()
    
    data_dict = {"rows": []}
    for row in data:
        data_dict["rows"].append(dict(zip(weather_data_fields, row)))
    print(json.dumps(jsonify(data_dict).json, indent=4))
             
    return render_template('weather.html', data=data)


@app.route("/weather/history", methods=["POST"])
def add_weather_history():
    data_dict = request.get_json()
    if data_dict is None:
        return jsonify({"error": "POST body empty"}), 400  # Bad request error
    
    data = data_dict.get("rows", None)
    if data is None:
        return jsonify({"error": "POST body doesn't have a 'rows' key"}), 422  # Unprocessable request error
    
    result = {"rows":[]}
    with sqlite3.connect("weather.db") as con:
        cur = con.cursor()
        for row in data:
            valid, values = validate_weather(row)
            if not valid:
                continue
            
            cur.execute("INSERT INTO weather_data (" + ", ".join(weather_data_fields) + \
                    " VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING rowid, *", values)
            result["rows"].append(dict(zip(weather_data_fields, cur.fetchone())))
        
        return jsonify(result), 201  # Successful entry creation code


@app.route("/weather/history/<int:rowid>", methods=["PUT"])
def update_weather_history(rowid: int):
    data_dict = request.get_json()
    if data_dict is None:
        return jsonify({"error": "POST body empty"}), 400  # Bad request error
    
    data = data_dict.get("rows", None)
    if data is None:
        return jsonify({"error": "POST body doesn't have a 'rows' key"}), 422  # Unprocessable request error
    
    result = {"rows":[]}
    with sqlite3.connect("weather.db") as con:
        cur = con.cursor()
        row = data[0]
        valid, values = validate_weather(row)
        if not valid:
            return jsonify({"error": "Invalid data in 'rows'"}), 422  # Unprocessable request error
        
        cur.execute("UPDATE weather_data SET " + ", ".join(values) + " WHERE rowid=" + str(rowid) + "RETURNING rowid, *")
        result["rows"].append(dict(zip(weather_data_fields, cur.fetchone())))
        
        return jsonify(result), 201  # Successful entry creation code


@app.route("/weather/history/<int:rowid>", methods=["DELETE"])
def delete_weather_history(rowid: int):
    result = {"rows":[]}
    with sqlite3.connect("weather.db") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM weather_data WHERE rowid=" + str(rowid) + "RETURNING rowid, *")
        result["rows"].append(dict(zip(weather_data_fields, cur.fetchone())))
        
        return jsonify(result), 201  # Successful entry creation code



if __name__ == "__main__":
    app.run(debug=False)