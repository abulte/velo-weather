import os

from datetime import date

import json
import requests
from colour import Color

from flask import Flask, render_template, request
from flask_babel import Babel, format_date, _


app = Flask(__name__)

app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['LANGUAGES'] = ['en', 'fr']

babel = Babel(app)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

app.jinja_env.globals['get_locale'] = get_locale

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
    _max = 30
    temp = temp if temp > 0 else 0
    temp = temp if temp < _max else temp
    c1 = Color("blue")
    c2 = Color("white")
    gradient_cold = list(c1.range_to(c2, ideal + 1))
    c1 = Color("white")
    c2 = Color("red")
    gradient_hot = list(c1.range_to(c2, _max + 1))
    gradient = gradient_cold + gradient_hot
    return gradient[int(temp)].hex


@app.template_filter("day")
def day(value, format="%A %d %b"):
    """Use Babel to localize a date from ISO with language-specific format"""
    if value is None:
        return ""
    d = date.fromisoformat(value)
    
    localized_format = _('EEEE, MMMM d')

    return format_date(date=d, format=localized_format)


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


@app.template_filter("localized_condition")
def localized_condition(code):
    """Translate weather condition from code"""
    
    # conditions list from https://www.weatherapi.com/docs/#weather-icons
    c_file = open('translations/conditions.json')
    c_data = json.loads(c_file.read())

    condition = next((item for item in c_data if item['code'] == code), None)

    for lang in condition['languages']:
        if lang['lang_iso'] == get_locale():
            localized_condition_text = lang['day_text']
            break
    else:
        localized_condition_text = condition['day']

    return localized_condition_text


@app.template_filter("localized_azimuth")
def localized_azimuth(code):
    """Translate azimuth from code"""
    
    # conditions list from https://www.weatherapi.com/docs/#weather-icons
    a_file = open('translations/azimuths.json')
    a_data = json.loads(a_file.read())

    azimuth = a_data[code][get_locale()]

    return azimuth
