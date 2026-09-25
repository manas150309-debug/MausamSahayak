# Manas - Data center and backend

| File | Role |
|---|---|
| `db.py` | SQLite schema (WAL mode), auto-migration |
| `ingest.py` | Validates telemetry; out-of-range values become NULL (sensor fault), never trusted; duplicate `(node, ts)` ignored |
| `service.py` | Rain sums, river rise rate, upstream state, risk assessment (calls Parul's engine), alert generation with de-escalation hold, nearest station, crop advice |
| `api.py` | Flask REST API + dashboard (`/dashboard`) |
| `mqtt_ingest.py` | MQTT subscriber (`mausam/nodes/+/telemetry`) + alert worker thread |
| `worker.py` | Alert check loop (every 60 s) |
| `cli.py` | `init-db`, `add-node`, `seed-demo`, `demo`, `serve`, `worker`, `ingest`, `alert-check` |
| `static/dashboard.html` | Live cards, sparklines, stale banner |

## API
| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | - | liveness |
| `GET /api/nodes` | - | stations |
| `GET /api/nodes/<id>/latest` | - | latest reading + stale flag |
| `GET /api/nodes/<id>/history?hours=24` | - | readings |
| `GET /api/nodes/<id>/risk` | - | flood + heat assessment with reasons and forecast |
| `GET /api/nearest?lat=&lon=` | - | nearest station and whether it is in range |
| `GET /api/crop-advice?lat=&lon=&irrigated=0/1` | - | crop suggestions |
| `GET /api/alerts?since_id=` | - | alert log (the bot polls this) |
| `POST /api/readings` | `X-API-Key` | HTTP alternative to MQTT |
| `POST /api/nodes` | `X-API-Key` | register a node (`node_id, lat, lon, danger_level_cm, upstream_node_id`) |

## Design decisions to explain in the viva
- **Fail-safe**: a node that stops reporting is UNKNOWN (ranked above GREEN), and a null sensor value is UNKNOWN, never zero.
- **Alerts on change only**, escalation immediate, de-escalation held 30 min so levels do not flap.
- **SQLite** is enough for a few nodes (5-minute readings = ~600 rows/day/node). Moving to PostgreSQL/InfluxDB means replacing `db.py` and the SQL in `service.py`.
- Forecast failures never stop monitoring.
- Stack note: the API uses **Flask** (not FastAPI as in the first plan document) so it could be fully tested in the build environment - update the report's software-stack line accordingly.
