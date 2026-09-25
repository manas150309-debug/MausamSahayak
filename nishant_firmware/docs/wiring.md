# Wiring (ESP32 DevKit)

| Sensor | Sensor pin | ESP32 pin | Notes |
|---|---|---|---|
| BME280 (I2C) | VIN / GND | 3V3 / GND | |
| | SDA / SCL | GPIO21 / GPIO22 | address 0x76 or 0x77 (`BME_ADDR`) |
| Rain gauge (reed switch) | one wire | GPIO27 | internal pull-up; other wire to GND |
| JSN-SR04T | VCC / GND | 5V / GND | needs 5 V; draws ~30 mA while pinging |
| | TRIG | GPIO5 | 3.3 V logic is accepted by the module |
| | ECHO | GPIO18 **via divider** | ECHO is 5 V. Use 1k (top) + 2k (bottom to GND), tap in the middle to the GPIO |
| Capacitive soil sensor v1.2 | VCC / GND | 3V3 / GND | |
| | AOUT | GPIO34 (ADC1) | do not use ADC2 pins - they stop working while Wi-Fi is on |
| Battery sense | 100k + 100k divider from battery + | GPIO35 (ADC1) | ratio 2.0 (`BATT_DIVIDER`); add 100 nF from GPIO35 to GND |

## Power
```
6 V solar panel -> charge controller / protection board -> 2 x 18650 (protected cells)
                                                            -> 5 V boost or buck-boost -> ESP32 5V/VIN and JSN-SR04T
```
- Use a charger board designed for Li-ion (CN3791 MPPT or TP4056 with protection). Never connect a raw solar panel to a Li-ion cell.
- A stock DevKit wastes 10-20 mA in the USB-serial chip and power LED even in sleep. For a real deployment cut the LED and use a low-quiescent regulator (or a bare ESP32 module) - measure it (see `power_budget.md`).
- Optional: switch the JSN-SR04T supply with a logic-level MOSFET so it draws nothing between readings.

## Layout tips
- Keep the ultrasonic sensor pointing straight down over open water, at least 30 cm away from walls or bridge piers, with nothing between it and the surface.
- Mount the BME280 in a ventilated radiation shield (stacked plates or a louvered box), out of direct sun, away from the solar panel and the enclosure walls.
- Drip loops on every cable; use IP65 cable glands.
