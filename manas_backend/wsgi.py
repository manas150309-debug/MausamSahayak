"""gunicorn entry point:  gunicorn manas_backend.wsgi:app"""
from parul_risk_crop.forecast import get_forecast

from .api import create_app

app = create_app(forecast_fn=get_forecast)
