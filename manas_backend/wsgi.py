"""Gunicorn entry point with an optional, idempotent presentation bootstrap."""
from parul_risk_crop.forecast import get_forecast

from .api import create_app
from .config import Settings
from . import db
from .cli import seed_demo

settings = Settings.from_env()

# Hosted demos start useful after every ephemeral-disk restart. Real deployments
# keep this off and ingest only authenticated field telemetry.
if settings.demo_mode:
    conn = db.connect(settings.db_path)
    db.init_db(conn)
    try:
        if conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] == 0:
            seed_demo(conn)
    finally:
        conn.close()

# A key enables live AccuWeather enrichment. Keyless hosted demos stay fast and
# deterministic; non-demo deployments retain the Open-Meteo fallback.
forecast_fn = get_forecast if settings.accuweather_api_key or not settings.demo_mode else None
app = create_app(settings=settings, forecast_fn=forecast_fn)
