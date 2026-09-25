"""Publish fake sensor data - use it while hardware is late, for demos, and for load tests (Nishant).

Replay mode (default): sends 288 readings covering the last 24 h, oldest first.
Realtime mode: sends one reading every --interval seconds, advancing the scenario.

Examples
  python -m nishant_firmware.simulator.simulate --node node01 --scenario flood --url http://localhost:8000 --api-key dev-key
  python -m nishant_firmware.simulator.simulate --node node01 --scenario normal --transport mqtt --broker localhost --realtime
"""
import argparse
import json
import random
import time

from . import scenarios


class HttpSender:
    def __init__(self, url, api_key):
        import requests
        self.s, self.url, self.key = requests, url.rstrip("/"), api_key

    def send(self, reading):
        r = self.s.post(f"{self.url}/api/readings", json=reading, headers={"X-API-Key": self.key}, timeout=10)
        return r.status_code


class MqttSender:
    def __init__(self, host, port, user, password):
        import paho.mqtt.client as mqtt
        try:
            self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:
            self.c = mqtt.Client()
        if user:
            self.c.username_pw_set(user, password)
        self.c.connect(host, port, 60)
        self.c.loop_start()

    def send(self, reading):
        info = self.c.publish(f"mausam/nodes/{reading['node_id']}/telemetry", json.dumps(reading), qos=0)
        return info.rc


def run(sender, node, scenario, realtime=False, interval=5.0, delay=0.0, count=None, log=print):
    now = int(time.time())
    if not realtime:
        for r in scenarios.backfill(scenario, node, now):
            log(f"{r['ts']} -> {sender.send(r)}  rain={r['rain_mm']} level={r['water_level_cm']}")
            if delay:
                time.sleep(delay)
        return
    rng, i = random.Random(), 0
    while count is None or i < count:
        p = min(1.0, i / (scenarios.INTERVALS - 1))
        r = scenarios.make_reading(scenario, p, int(time.time()), rng, node)
        log(f"{r['ts']} -> {sender.send(r)}  rain={r['rain_mm']} level={r['water_level_cm']}")
        i += 1
        time.sleep(interval)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", default="node01")
    ap.add_argument("--scenario", choices=scenarios.SCENARIOS, default="normal")
    ap.add_argument("--transport", choices=("http", "mqtt"), default="http")
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--api-key", default="dev-key")
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--mqtt-user", default="")
    ap.add_argument("--mqtt-password", default="")
    ap.add_argument("--realtime", action="store_true")
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between replayed readings")
    a = ap.parse_args(argv)
    sender = HttpSender(a.url, a.api_key) if a.transport == "http" else MqttSender(a.broker, a.port, a.mqtt_user, a.mqtt_password)
    run(sender, a.node, a.scenario, a.realtime, a.interval, a.delay)


if __name__ == "__main__":
    main()
