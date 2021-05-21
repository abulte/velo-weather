import os

from datetime import date

import requests
from colour import Color

from flask import Flask, render_template


app = Flask(__name__)


# top of the scale for wind, kph
MAX_WIND_ACCEPTABLE = 35
# top of the scale for rain, mm per hour
MAX_RAIN_ACCEPTABLE = 1.5


@app.route("/")
def index():
    api_key = os.getenv("WEATHER_API_KEY")
    q = "Poissy, France"
    r = requests.get(f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={q}&days=10&aqi=no&alerts=yes")
    r.raise_for_status()
    data = r.json()
    return render_template("index.html", data=data, max_rain=MAX_RAIN_ACCEPTABLE)


@app.template_filter("gradient")
def gradient(value, max, end="red"):
    """With a value from 0 to max, generate the correct gradient"""
    value = int(value)
    c1 = Color("white")
    c2 = Color(end)
    gradient = list(c1.range_to(c2, max + 1))
    value = value if value < max else value
    return gradient[int(value)].hex


@app.template_filter("day")
def day(value, format="%A %d %b"):
    """Format a date from ISO"""
    if value is None:
        return ""
    d = date.fromisoformat(value)
    return d.strftime(format)


@app.template_filter("proba")
def proba(hour):
    """Compute a proba and output gradient color"""
    chance = int(hour["chance_of_rain"]) / 100
    precip = min(hour["precip_mm"], MAX_RAIN_ACCEPTABLE)
    wind = min(hour["wind_kph"], MAX_WIND_ACCEPTABLE)

    p_precip = (chance * precip) / MAX_RAIN_ACCEPTABLE
    p_wind = wind / MAX_WIND_ACCEPTABLE
    # wind is twice as annoying as rain
    p = (p_precip + p_wind * 2) / 3

    return gradient((1 - p) * 100, max=100, end="green")
