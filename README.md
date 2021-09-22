# velo-weather

**Bike ride opportunity, according to rain and wind forecasts where you are.**

This uses https://www.weatherapi.com/ for weather forecast, you'll need to set `WEATHER_API_KEY` env var to build your own instance.

Apart from that, it's just a standard Flask app :-). It can be deployed on Dokku and Heroku.

## Translations

Initialize a new language:

```bash
pybabel init -i translations/messages.pot -d translations -l fr
```

Update all translation files:

```bash
pybabel extract -F babel.cfg -k _l -o translations/messages.pot .
pybabel update -i translations/messages.pot -d translations
```

Compile translation files:

```bash
pybabel compile -d translations
```
