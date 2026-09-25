"""Command line helper (Manas).

  python -m manas_backend.cli init-db
  python -m manas_backend.cli add-node node01 "Campus" 28.4089 77.3178 --district Faridabad --state Haryana --danger 450
  python -m manas_backend.cli seed-demo          # 3 demo nodes with 24 h of synthetic data
  python -m manas_backend.cli alert-check        # run one alert pass
  python -m manas_backend.cli serve              # API + dashboard on :8000 (dev server)
  python -m manas_backend.cli demo               # seed-demo + serve
  python -m manas_backend.cli worker | ingest
"""
import argparse
import logging
import time
import zlib

from nishant_firmware.simulator import scenarios

from . import db, ingest, service
from .config import Settings

DEMO_NODES = [
    # node_id, name, lat, lon, danger_cm, scenario   (coordinates are approximate demo values)
    ("node01", "Campus drain (demo)", 28.4089, 77.3178, 300.0, "normal"),
    ("node02", "Riverbank site (demo)", 28.3700, 77.3800, 450.0, "flood"),
    ("node03", "Village pond (demo)", 28.4600, 77.2900, 400.0, "silent"),
]


def seed_demo(conn, now=None, scenario_override=None):
    now = int(now if now is not None else time.time())
    for node_id, name, lat, lon, danger, scen in DEMO_NODES:
        service.add_node(conn, node_id, name, lat, lon, "Faridabad", "Haryana", danger, now)
        for r in scenarios.backfill(scenario_override or scen, node_id, now, seed=zlib.crc32(node_id.encode())):
            ingest.store_reading(conn, node_id, r, now)
    return len(DEMO_NODES)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    a = sub.add_parser("add-node")
    a.add_argument("node_id"); a.add_argument("name"); a.add_argument("lat", type=float); a.add_argument("lon", type=float)
    a.add_argument("--district"); a.add_argument("--state"); a.add_argument("--danger", type=float, help="danger-mark water level in cm")
    a.add_argument("--upstream", help="node_id of the node upstream on the same river")
    for name in ("seed-demo", "demo"):
        s = sub.add_parser(name)
        s.add_argument("--scenario", choices=scenarios.SCENARIOS, help="force one scenario on every demo node")
    sub.add_parser("alert-check"); sub.add_parser("serve"); sub.add_parser("worker"); sub.add_parser("ingest")
    args = ap.parse_args(argv)
    settings = Settings.from_env()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.cmd in ("worker", "ingest"):
        if args.cmd == "worker":
            from . import worker
            worker.loop(settings)
        else:
            from . import mqtt_ingest
            mqtt_ingest.main(settings)
        return
    conn = db.connect(settings.db_path)
    db.init_db(conn)
    if args.cmd == "init-db":
        print("database ready at", settings.db_path)
    elif args.cmd == "add-node":
        service.add_node(conn, args.node_id, args.name, args.lat, args.lon, args.district, args.state, args.danger,
                         upstream_node_id=args.upstream)
        print("saved", args.node_id)
    elif args.cmd in ("seed-demo", "demo"):
        print(f"seeded {seed_demo(conn, scenario_override=args.scenario)} demo nodes into {settings.db_path}")
    elif args.cmd == "alert-check":
        from . import worker
        for al in worker.run_once(settings):
            print(al)
    if args.cmd in ("serve", "demo"):
        import dataclasses
        from parul_risk_crop.forecast import get_forecast
        from .api import create_app
        if not settings.api_key:
            settings = dataclasses.replace(settings, api_key="dev-key")
            print("MAUSAM_API_KEY not set - using 'dev-key' for this dev session only")
        app = create_app(settings, forecast_fn=get_forecast)
        if args.cmd == "demo":
            import threading
            from . import worker
            threading.Thread(target=worker.loop, args=(settings,), daemon=True).start()
        print("dashboard: http://localhost:8000/dashboard")
        app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
