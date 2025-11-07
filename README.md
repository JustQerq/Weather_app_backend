# Overview
Backend for a weather application by Oleg Samarets.
- Written in Python Flask
- Supports all the CRUD operations for an internal SQLite database
- Ensures secure data transfer via RESTful API

# How to run
1. Clone this repository
2. `python -m venv .venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python run_waitress.py`
6. Open `http://localhost:8080/` in browser
7. Use various API endpoints (listed below) or run the frontend App: https://github.com/JustQerq/weather-app

# REST API
- `GET http://localhost:8080/weather/current?city=&country=&latitude=&longitude=`
  - Params: "city", "country", "latitude", "longitude"
- `GET /weather/history/<int:rowid>`
- `GET http://localhost:8080/weather/history?...`
  - Search by value params: "rowid", "datetime", "city", "country", "latitude", "longitude", "temperature_c", "feelslike_c", "humidity", "condition", "wind_kph"
  - Filtering search from ( >= ) params: "datetime_gr", "temperature_c_gr", "feelslike_c_gr", "humidity_gr", "wind_kph_gr"
  - Filtering search to ( <= ) params: "datetime_ls", "temperature_c_ls", "feelslike_c_ls", "humidity_ls", "wind_kph_ls"
- `POST http://localhost:8080/weather/history`
  - body: {'rows': [{"datetime":val, "city":val, "country":val, "latitude":val, "longitude":val, "temperature_c":val, "feelslike_c":val, "humidity":val, "condition":val, "wind_kph":val}, ...]}
- `PUT /weather/history/<int:rowid>`
  - body: {"datetime":val, "city":val, "country":val, "latitude":val, "longitude":val, "temperature_c":val, "feelslike_c":val, "humidity":val, "condition":val, "wind_kph":val}
- `DELETE /weather/history/<int:rowid>`
- `GET http://localhost:8080/weather/forecast?...`
  - Params: "city", "country", "latitude", "longitude"
