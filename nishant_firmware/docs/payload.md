# Telemetry contract (node -> backend)

Topic: `mausam/nodes/<node_id>/telemetry` (MQTT, QoS 0). The same JSON can be POSTed to `POST /api/readings` with header `X-API-Key`.

```json
{
  "node_id": "node01",
  "ts": 1790000000,
  "temperature_c": 31.4,
  "humidity_pct": 62.0,
  "pressure_hpa": 1003.2,
  "rain_mm": 0.56,
  "water_level_cm": 132.5,
  "soil_moisture_pct": 41.0,
  "battery_v": 3.92,
  "rssi": -71
}
```

| Field | Meaning | Accepted range (else stored as NULL = sensor fault) |
|---|---|---|
| `ts` | UTC epoch seconds of the reading (ms also accepted). Optional; if missing or more than 7 days old / 10 min in the future the server time is used | - |
| `rain_mm` | rain in **this interval** (tips x mm per tip), not a running total | 0 - 200 |
| `water_level_cm` | height of water above the reference zero (`SENSOR_HEIGHT_CM - distance`) | 0 - 3000 |
| `temperature_c` | air temperature | -40 - 70 |
| `humidity_pct` | relative humidity | 0 - 100 |
| `pressure_hpa` | station pressure | 800 - 1100 |
| `soil_moisture_pct` | relative soil wetness | 0 - 100 |
| `battery_v` | battery voltage | 2.5 - 5.5 |

Send `null` for a sensor that failed. **Never send 0 as a stand-in** - a fake 0 looks like "no rain / dry river" and hides the fault.
A reading with the same `(node_id, ts)` is ignored, so re-sending buffered data is safe.
