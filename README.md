# MausamSahayak - IoT weather, flood alert and crop advisory system

B.Tech capstone 2026-27. Team, in order: **Manas, Parul, Nishant, Swati, Anil.**

Outdoor sensor nodes -> MQTT -> backend with live dashboard -> risk engine (flood, heat, crop) -> Hindi/English Telegram bot with SMS fallback.
A silent or faulty sensor is reported as **UNKNOWN, never "all clear"**. The bot only **advises** and points to the authorities (112, NDMA 1078, district administration).

## Who owns what
| # | Person | Folder | Role |
|---|---|---|---|
| 1 | Manas | `manas_backend/` | MQTT ingest, database, REST API, live dashboard, alert generation, stale-data handling |
| 2 | Parul | `parul_risk_crop/` | Flood/heat rules, forecast client, crop advisor (rules + Random Forest), threshold validation |
| 3 | Nishant | `nishant_firmware/` | ESP32 firmware, wiring/calibration/power docs, sensor simulator |
| 4 | Swati | `swati_bot/` | Telegram bot, Hindi/English text, alert delivery, SMS fallback, user-trial support |
| 5 | Anil | `anil_docs/` | Data sources, site selection, budget, KVK validation, user trial, poster/presentation/viva/paper docs, Assam case study |

## Try it in 2 minutes (no hardware)
```bash
pip install -r requirements.txt
python -m unittest discover -s . -t . -p "test_*.py"     # 108 tests
python -m manas_backend.cli demo                         # seeds 3 demo stations, serves http://localhost:8000/dashboard
```
The demo shows one GREEN station, one RED (flood) station and one UNKNOWN (silent) station. To feed a station from the simulator:
`python -m nishant_firmware.simulator.simulate --node node01 --scenario heavy_rain --url http://localhost:8000 --api-key dev-key`
Bot: `TELEGRAM_TOKEN=... API_BASE_URL=http://localhost:8000 python -m swati_bot.bot`

## What is verified and what is not (be honest in the viva)
| Part | Status |
|---|---|
| Risk engine, crop advisor, forecast parser, validation and ML pipelines | Unit-tested (synthetic data only for validation/ML pipelines) |
| Backend ingest, alerts, REST API, dashboard | Unit-tested and smoke-tested against a live local server |
| Bot conversation logic, Hindi/English text, alert routing, SMS logic | Unit-tested, including end-to-end against the real API in-process |
| `swati_bot/bot.py` Telegram glue | **Not run** - needs a real bot token; expect small fixes |
| ESP32 firmware | **Not compiled or run on hardware** - build, then verify sleep timing, rain counting while asleep, ultrasonic level |
| `deploy/` Docker files, MQTT broker config | **Not run** |
| MQTT ingester (`mqtt_ingest.py`) | Message handling tested; live broker connection **not run** |
| Thresholds, crop ranges, district rainfall normals | **Starting values / placeholders** - must be calibrated and KVK-reviewed |
| Hindi text | Needs review by a native speaker before the user trial |
| Assamese | Not supported |

## Real data you still must collect
1. Real historical rain + flood dates -> `anil_docs/tools/fetch_historical_rain.py` -> `parul_risk_crop.validate_thresholds` (files named `*_SYNTHETIC.csv` are for testing code only; never quote their numbers).
2. Sensor calibration and accuracy tables (`nishant_firmware/docs/calibration.md`).
3. KVK crop review and a 10+ person bot trial (`anil_docs/docs/`).

## Repository size
About 3,800 lines of code and configuration (about 900 of them tests) plus documentation. The size is what the design needs; nothing is padded.
