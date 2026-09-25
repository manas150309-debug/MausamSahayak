"""Periodic alert check (Manas). Runs forever; safe to run alongside the MQTT ingester."""
import logging
import time

from parul_risk_crop.forecast import get_forecast

from . import db, service
from .config import Settings

log = logging.getLogger("worker")


def run_once(settings: Settings, forecast_fn=get_forecast, now=None):
    conn = db.connect(settings.db_path)
    try:
        db.init_db(conn)
        created = service.run_alert_check(conn, int(now if now is not None else time.time()), forecast_fn, settings)
        for a in created:
            log.warning("ALERT node=%s kind=%s %s -> %s stale=%s", a["node_id"], a["kind"],
                        a["previous_level_name"], a["level_name"], a["stale"])
        return created
    finally:
        conn.close()


def loop(settings: Settings, forecast_fn=get_forecast):
    log.info("alert worker started, interval %ss", settings.worker_interval_s)
    while True:
        try:
            run_once(settings, forecast_fn)
        except Exception:                      # never let one bad cycle kill monitoring
            log.exception("alert check failed")
        time.sleep(settings.worker_interval_s)
