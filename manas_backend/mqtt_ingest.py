"""MQTT subscriber that stores telemetry (Manas). Requires paho-mqtt (pip install paho-mqtt).

Topic:  mausam/nodes/<node_id>/telemetry     payload: JSON (see nishant_firmware/docs/payload.md)
"""
import logging
import threading

from . import db, ingest, worker
from .config import Settings

log = logging.getLogger("mqtt_ingest")
TOPIC = "mausam/nodes/+/telemetry"


def main(settings: Settings = None, with_worker: bool = True):
    import paho.mqtt.client as mqtt          # imported lazily so the rest of the package works without it

    settings = settings or Settings.from_env()
    conn = db.connect(settings.db_path)
    db.init_db(conn)

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="mausam-ingest")
        v2 = True
    except AttributeError:                  # paho-mqtt 1.x
        client = mqtt.Client(client_id="mausam-ingest")
        v2 = False
    if settings.mqtt_user:
        client.username_pw_set(settings.mqtt_user, settings.mqtt_password)

    def on_connect(c, userdata, flags, rc, *extra):
        log.info("connected to broker (rc=%s), subscribing to %s", rc, TOPIC)
        c.subscribe(TOPIC, qos=0)           # (re)subscribe on every reconnect

    def on_message(c, userdata, msg):
        try:
            res = ingest.handle_message(conn, msg.topic, msg.payload)
            if not res.ok:
                log.warning("rejected %s: %s", msg.topic, res.reason)
            elif res.dropped_fields:
                log.warning("%s dropped out-of-range fields: %s", msg.topic, res.dropped_fields)
        except Exception:
            log.exception("failed to process message on %s", msg.topic)

    client.on_connect, client.on_message = on_connect, on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    if with_worker:
        threading.Thread(target=worker.loop, args=(settings,), daemon=True).start()
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()
