# Nishant - Sensor nodes, firmware, power, enclosure

| Path | What it is |
|---|---|
| `firmware/` | PlatformIO project for the ESP32 node (BME280, rain gauge, JSN-SR04T, soil, battery, Wi-Fi + MQTT, offline buffer, light sleep) |
| `simulator/` | Python fake-sensor publisher (HTTP or MQTT) - use it while hardware is late and for the exhibition backup demo |
| `docs/wiring.md` | Pin map, level shifting, power wiring |
| `docs/calibration.md` | How to calibrate rain, water level, soil, battery and how to record the accuracy numbers for the report |
| `docs/payload.md` | The JSON contract with Manas's backend |
| `docs/power_budget.md` | Battery/solar sizing worked example |
| `docs/deployment_checklist.md` | Enclosure and field-install checklist |

## Status (read this)
- The **simulator** and its tests run today: `python -m unittest discover -s nishant_firmware -t .`
- The **firmware** has NOT been compiled or run on hardware yet. Build it, fix small API differences, and verify:
  1. light-sleep timing (does `esp_timer_get_time()` keep counting through sleep on your core version?)
  2. rain tips are counted while asleep (tip the bucket by hand 10 times, expect 10 x `MM_PER_TIP`)
  3. JSN-SR04T readings through the level shifter
- GSM transport is **not implemented** (Wi-Fi only). Extension point: replace `connectWifi()` / the `WiFiClient` with a TinyGSM client.

## Build and flash
```bash
cd nishant_firmware/firmware
# edit include/config.h (NODE_ID, Wi-Fi, MQTT, SENSOR_HEIGHT_CM, calibration)
pio run -t upload
pio device monitor
```
Register the same `NODE_ID` in the backend first (`python -m manas_backend.cli add-node ...`), otherwise messages are rejected as `unknown_node`.

## No hardware yet?
```bash
python -m manas_backend.cli demo                                   # terminal 1
python -m nishant_firmware.simulator.simulate --node node01 --scenario flood   # terminal 2 (needs node01 registered; demo does it)
```
