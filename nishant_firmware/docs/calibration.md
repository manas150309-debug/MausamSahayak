# Calibration and accuracy testing

These are the numbers for the "Sensor accuracy" row in the report. Record every test in a table (date, reference reading, node reading, error).

## 1. Temperature and humidity (BME280)
- Place the node next to a reference thermometer / hygrometer (a good handheld or a nearby IMD/AWS station) for 24 h, sampling every 5 min.
- Report mean absolute error and maximum error for temperature and RH. Typical BME280 is about +/-1 C and +/-3 % RH; on-board self-heating adds error, so keep it in a shield.

## 2. Rain gauge
- Fill a measuring cylinder with a known volume `V` (mL). Gauge funnel area `A` (cm^2) gives depth `mm = V / A / 10`.
- Pour slowly through the funnel and count tips `n`. Then `MM_PER_TIP = depth_mm / n`. Update `config.h` and `scenarios.py`.
- Repeat at 3 pour rates (slow, medium, fast) - tipping buckets under-read at high intensity. Report the error at each rate.

## 3. Water level (ultrasonic)
- Mount the sensor over a water tank. Measure the real distance with a tape at 5-6 levels (30 cm to 400 cm).
- Compare with the reading, report error. Set `SENSOR_HEIGHT_CM` so that `level = height - distance` matches the gauge/staff at the site; the backend's `danger_level_cm` for the node must use the same zero.
- Check readings when it rains (droplets) and in wind (ripples). The median-of-7 filter should hide most noise; report the spread.

## 4. Soil moisture
- Read the raw ADC value with the sensor in dry air (`SOIL_RAW_DRY`) and submerged up to the line in water (`SOIL_RAW_WET`).
- The output is a relative wetness index. For a real volumetric % compare against oven-dried soil samples (weigh wet, dry at 105 C for 24 h, compute water content) and fit a line.

## 5. Battery
- Compare the reported voltage with a multimeter at full, mid and low charge; adjust `BATT_DIVIDER` if it is off by more than 2 %.

## 6. System tests to log
| Test | Pass criterion |
|---|---|
| Node powered from battery for 3 days without sun | still reporting |
| Wi-Fi off for 1 h then on | all buffered readings arrive, no duplicates in the database |
| Unplug the ultrasonic sensor | reading goes null, backend shows UNKNOWN (not GREEN) |
| Power off the node | backend flags "station not reporting" after 30 min |
| Tip the bucket 20 times during sleep | 20 x `MM_PER_TIP` recorded |
