from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import sqlite3
from requests_manager import WeatherRequestsManager
from database_manager import params2sql, validate_weather
import json
import datetime


app = Flask(__name__)
CORS(app)
weather_req_manager = WeatherRequestsManager()
weather_data_fields = ["rowid", "datetime", "city", "country", "latitude", "longitude", "temperature_c", \
        "feelslike_c", "humidity", "condition", "wind_kph"]
weather_forecast_fields = ["date", "city", "country", "latitude", "longitude", "temperature_min_c", \
        "temperature_max_c", "temperature_avg_c", "humidity_avg", "condition", "wind_max_kph"]


@app.route('/')
@app.route('/home')
def index():
    return render_template('index_html')


@app.route('/weather/current', methods=["GET"])
def get_weather_current():
    data_response = None
    
    _, location_valid, _, request_args_validated = validate_weather(request.args)
    if not location_valid:
        print(request.args)
        return jsonify({"error": "location data invalid"}), 422
    
    value_city = request_args_validated[1]
    if value_city is not None:
        value_country = request_args_validated[2]
        if value_country is not None:
            data_response = weather_req_manager.get("current", q=f"{value_city}, {value_country}")
        else:
            data_response = weather_req_manager.get("current", q=value_city)
    else:
        value_latitude = request_args_validated[3]
        value_longitude = request_args_validated[4]
        
        if (value_latitude is not None) and (value_longitude is not None):
            data_response = weather_req_manager.get("current", q=f"{value_latitude},{value_longitude}")
    
    
    data = []
    if (data_response is not None) and (data_response.get("error", None) is None):
        data.append(data_response["current"]["last_updated"])
        data.append(data_response["location"]["name"])
        data.append(data_response["location"]["country"])
        data.append(data_response["location"]["lat"])
        data.append(data_response["location"]["lon"])
        data.append(data_response["current"]["temp_c"])
        data.append(data_response["current"]["feelslike_c"])
        data.append(data_response["current"]["humidity"])
        data.append(data_response["current"]["condition"]["text"])
        data.append(data_response["current"]["wind_kph"])
        
        with sqlite3.connect('weather.db') as con:
            cur = con.cursor()
            
            # Look for an existing entry in the database 
            # (can happen if no updates on the current weather have been made recently)
            cur.execute("SELECT rowid, * FROM weather_data WHERE datetime=" + \
                f'"{data_response["current"]["last_updated"]}"' + " AND latitude=" + \
                    str(data_response["location"]["lat"]) + " AND longitude=" + \
                        str(data_response["location"]["lon"]))
            data_returning = cur.fetchone()
            # If no matching entry found, save the new weather info into the database
            if data_returning is None:
                cur.execute("INSERT INTO weather_data \
                    (datetime, city, country, latitude, longitude, temperature_c, \
                        feelslike_c, humidity, condition, wind_kph) \
                            VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING rowid, *", data)
                # Using the data from RETURNING clause to get the inserted row id
                data_returning = cur.fetchone()
                con.commit()
        
    result = {"row": dict(zip(weather_data_fields, data_returning))}
    # return render_template('weather.html', data=data_returning)
    return jsonify(result), 200


@app.route('/weather/history/<int:rowid>', methods=['GET'])
def get_weather_history(rowid):
    with sqlite3.connect("weather.db") as con:
        cur = con.cursor()
        cur.execute("SELECT rowid, * FROM weather_data WHERE rowid=" + str(rowid))
        data = cur.fetchone()
        if data is not None:
            result = {"rows": [dict(zip(weather_data_fields, data))]}
        else:
            return jsonify({"error": "Record with the specified ID not found"}), 404
    return jsonify(result), 200


@app.route('/weather/history', methods=['GET'])
def get_weather_history_search():
    conditions = []
    
    # Equality conditionals (e.g. WHERE field = value)
    params_eq_dtypes = {"datetime": str, "city": str, "country": str, "latitude": float, "longitude": float, "temperature_c": float, \
            "feelslike_c": float, "humidity": float, "condition": str, "wind_kph": float}
    conditions += params2sql(received_params=request.args, params_dtypes=params_eq_dtypes, relationship="=")
    
    # Greater conditionals (e.g. WHERE field > value)
    params_gr_dtypes = {"datetime_gr": str, "temperature_c_gr": float, "feelslike_c_gr": float, "humidity_gr": float, "wind_kph_gr": float}
    params_gr_aliases = {"datetime_gr": "datetime", "temperature_c_gr": "temperature_c", \
        "feelslike_c_gr": "feelslike_c", "humidity_gr": "humidity", "wind_kph_gr": "wind_kph"}
    conditions += params2sql(received_params=request.args, params_dtypes=params_gr_dtypes, params_aliases=params_gr_aliases, relationship=">=")
            
    # Less conditionals (e.g. WHERE field < value)
    params_ls_dtypes = {"datetime_ls": str, "temperature_c_ls": float, "feelslike_c_ls": float, "humidity_ls": float, "wind_kph_ls": float}
    params_ls_aliases = {"datetime_ls": "datetime", "temperature_c_ls": "temperature_c", \
        "feelslike_c_ls": "feelslike_c", "humidity_ls": "humidity", "wind_kph_ls": "wind_kph"}
    conditions += params2sql(received_params=request.args, params_dtypes=params_ls_dtypes, params_aliases=params_ls_aliases, relationship="<=")
    
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
    # print(json.dumps(jsonify(data_dict).json, indent=4))
             
    #return render_template('weather.html', data=data)
    return jsonify(data_dict)


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
            datetime_valid, location_valid, data_valid, values = validate_weather(row)
            if not (datetime_valid and location_valid and data_valid):
                continue
            
            cur.execute("INSERT INTO weather_data (" + ", ".join(weather_data_fields[1:]) + \
                    ") VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING rowid, *", values)
            result["rows"].append(dict(zip(weather_data_fields, cur.fetchone())))
        
    return jsonify(result), 201  # Successful entry creation code


@app.route("/weather/history/<int:rowid>", methods=["PUT"])
def update_weather_history(rowid: int):
    data = request.get_json()
    
    if data is None:
        return jsonify({"error": "POST body empty"}), 400  # Bad request status code
    
    datetime_valid, location_valid, data_valid, values = validate_weather(data)
    if not (datetime_valid and location_valid and data_valid):
        return jsonify({"error": "invalid data"}), 422  # Unprocessable request error
    
    
    field_dtypes = {"datetime": str, "city": str, "country": str, "latitude": float, "longitude": float, "temperature_c": float, \
            "feelslike_c": float, "humidity": float, "condition": str, "wind_kph": float}
    conditions = params2sql(received_params=dict(zip(weather_data_fields[1:], values)), params_dtypes=field_dtypes, relationship="=")
    
    with sqlite3.connect("weather.db") as con:
        cur = con.cursor()
        print("UPDATE weather_data SET " + ", ".join(conditions) + " WHERE rowid=" + str(rowid) + " RETURNING rowid, *")
        cur.execute("UPDATE weather_data SET " + ", ".join(conditions) + " WHERE rowid=" + str(rowid) + " RETURNING rowid, *")
        result = {"rows": [dict(zip(weather_data_fields, cur.fetchone()))]}
    
    return jsonify(result), 200  # Successful update with return status code


@app.route("/weather/history/<int:rowid>", methods=["DELETE"])
def delete_weather_history(rowid: int):
    with sqlite3.connect("weather.db") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM weather_data WHERE rowid=" + str(rowid) + " RETURNING rowid, *")
        
        result = {"rows": [dict(zip(weather_data_fields, cur.fetchone()))]}
    return jsonify(result), 200  # Successful delete with return status code


@app.route("/weather/forecast", methods=['GET'])
def get_weather_forecast():
    forecast_days = request.args.get("days", 3)
    data_response = None
    
    _, location_valid, _, request_args_validated = validate_weather(request.args)
    if not location_valid:
        return jsonify({"error": "location data invalid"}), 422
    
    value_city = request_args_validated[1]
    if value_city is not None:
        value_country = request_args_validated[2]
        if value_country is not None:
            data_response = weather_req_manager.get("forecast", q=f"{value_city}, {value_country}", days=forecast_days)
        else:
            data_response = weather_req_manager.get("forecast", q=value_city, days=forecast_days)
    else:
        value_latitude = request_args_validated[3]
        value_longitude = request_args_validated[4]
        
        if (value_latitude is not None) and (value_longitude is not None):
            data_response = weather_req_manager.get("forecast", q=f"{value_latitude},{value_longitude}", days=forecast_days)
    
      
    data = []
    if (data_response is not None) and (data_response.get("error", None) is None):
        for day in data_response["forecast"]["forecastday"]:
            daily_data = []
            daily_data.append(day["date"])
            daily_data.append(data_response["location"]["name"])
            daily_data.append(data_response["location"]["country"])
            daily_data.append(data_response["location"]["lat"])
            daily_data.append(data_response["location"]["lon"])
            daily_data.append(day["day"]["mintemp_c"])
            daily_data.append(day["day"]["maxtemp_c"])
            daily_data.append(day["day"]["avgtemp_c"])
            daily_data.append(day["day"]["avghumidity"])
            daily_data.append(day["day"]["condition"]["text"])
            daily_data.append(day["day"]["maxwind_kph"])
            data.append(dict(zip(weather_forecast_fields, daily_data)))
    
    result = {"rows": data}
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=False)