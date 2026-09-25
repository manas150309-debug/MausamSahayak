# Enclosure and field deployment checklist

## Before leaving the lab
- [ ] `NODE_ID`, Wi-Fi/MQTT credentials and `SENSOR_HEIGHT_CM` set for this site; node registered in the backend
- [ ] Calibration values recorded in `calibration.md` tables
- [ ] 24 h bench run with no gaps in the dashboard
- [ ] All cable glands tightened, silica gel pack inside the box, lid gasket seated
- [ ] Spare battery, spare rain-gauge funnel screen, cable ties, tape measure, multimeter, laptop

## At the site (get written permission first - see `anil_docs/docs/site_selection.md`)
- [ ] Rain gauge level (use a spirit level), funnel clear, at least twice its height away from walls/trees
- [ ] Ultrasonic sensor straight down, clear of structures, height above riverbed measured twice and written on the box
- [ ] Solar panel faces south, tilted about the site latitude, not shaded
- [ ] BME280 in a shield, not touching the enclosure
- [ ] Photo of every sensor in place and a GPS coordinate for the backend node entry
- [ ] Watch the dashboard until 3 readings have arrived from the field

## Maintenance visits (weekly during the project)
- [ ] Clean the funnel and the solar panel, check for insects in the bucket
- [ ] Compare rain with the reference gauge or the nearest IMD station
- [ ] Read battery voltage trend; replace cells below 3.5 V at dawn
