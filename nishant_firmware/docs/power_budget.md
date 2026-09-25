# Power budget (worked estimate - MEASURE before you trust it)

Assumptions: one cycle every 300 s.

| State | Current | Time per cycle | Charge per cycle |
|---|---|---|---|
| Wi-Fi + MQTT + sensors active | ~130 mA | ~12 s | 1.56 mAs x 1000 = 1560 mAs |
| Ultrasonic pings (7 x 70 ms) | ~30 mA extra | ~0.5 s | 15 mAs |
| Light sleep (bare module) | ~1 mA | ~287 s | 287 mAs |
| **Total** | | 300 s | ~1860 mAs -> **~6.2 mA average** |

- Per day: 6.2 mA x 24 h ~ **150 mAh**.
- Two 18650 cells (2 x 2600 mAh, ~70 % usable) ~ 3600 mAh -> about **24 days** with no sun.
- Solar: a 6 V / 2 W panel gives roughly 300 mA in full sun. With 4 peak-sun-hours and ~50 % system efficiency ~ 600 mAh/day, comfortably above 150 mAh/day even in monsoon cloud (about 25 % output).
- On a stock DevKit sleep current is 10-20 mA, which turns 150 mAh/day into 400-600 mAh/day. Measure with a multimeter in series and update this table.

How to measure: put a multimeter (or a USB power meter) in series with the supply, log the sleep current and the peak current during publish, and log battery voltage over 3 days to plot the discharge/charge curve for the report.
