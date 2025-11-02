from flask import Flask, render_template, request
import sqlite3


app = Flask(__name__)

@app.route('/')
@app.route('/home')
def index():
    return render_template('index_html')

@app.route('/weather', methods=['GET'])
def get_weather():
    con = sqlite3.connect('weather.db')
    cur = con.cursor()
    cur.execute('SELECT datetime, city, country, temperature, temperature_feels, humidity, condition, wind FROM weather_data')
    data = cur.fetchall()
    return render_template('weather.html', data=data)