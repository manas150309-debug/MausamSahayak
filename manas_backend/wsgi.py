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

# Demo deployments stay deterministic and fast even when the third-party
# forecast provider is unavailable; real deployments keep forecast enrichment.
app = create_app(settings=settings, forecast_fn=None if settings.demo_mode else get_forecast)
