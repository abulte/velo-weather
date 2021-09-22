import os

from datetime import date

import requests
from colour import Color

from flask import Flask, render_template, request


app = Flask(__name__)


# top of the scale for wind, kph
MAX_WIND_ACCEPTABLE = 35
# top of the scale for rain, mm per hour
MAX_RAIN_ACCEPTABLE = 1.5


@app.route("/")
def index():
    data = None
    q = request.args.get("location", "Poissy, France")
    api_key = os.getenv("WEATHER_API_KEY")
    r = requests.get(f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={q}&days=10&aqi=no&alerts=yes")
    # probably location unknow
    if r.status_code != 400:
        r.raise_for_status()
        data = r.json()
    return render_template("index.html", data=data, max_rain=MAX_RAIN_ACCEPTABLE, max_wind=MAX_WIND_ACCEPTABLE)


@app.template_filter("gradient")
def gradient(value, max, end="red"):
    """With a value from 0 to max, generate the correct gradient"""
    value = int(value)
    c1 = Color("white")
    c2 = Color(end)
    gradient = list(c1.range_to(c2, max + 1))
    value = value if value < max else value
    return gradient[int(value)].hex


@app.template_filter("gradient_precip")
def gradient_precip(precip_mm):
    """Handle gradient for precip_mm"""
    precip = min(precip_mm, MAX_RAIN_ACCEPTABLE)
    return gradient(precip * 100, int(MAX_RAIN_ACCEPTABLE * 100))


@app.template_filter("gradient_temp")
def gradient_temp(temp, ideal):
    """Handle gradient for temp around ideal temp"""
    _max = 35
    temp = temp if temp > 0 else 0
    temp = temp if temp < _max else temp

    gradient = []

    for temperature in range(ideal):
        temp_luminance = 50 + (50 / ideal) * temperature
        gradient.append("hsl(220,100%,{}%)".format(round(temp_luminance)))

    for temperature in range(_max - ideal + 1):
        temp_luminance = 100 - (50 / (_max - ideal + 1)) * temperature
        gradient.append("hsl(0,100%,{}%)".format(round(temp_luminance)))

    gradient.append("hsl(0,100%,50%)")

    return gradient[round(temp)]


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
