#pragma once
// ---------------------------------------------------------------------------
// Per-node configuration. Edit for each station. DO NOT commit real passwords.
// ---------------------------------------------------------------------------

// identity - must match the node registered in the backend (letters, digits, _ or -, max 32)
#define NODE_ID            "node01"

// network
#define WIFI_SSID          "CHANGE_ME"
#define WIFI_PASSWORD      "CHANGE_ME"
#define MQTT_HOST          "192.168.1.10"     // your MQTT broker / cloud server
#define MQTT_PORT          1883
#define MQTT_USER          "node01"
#define MQTT_PASSWORD      "CHANGE_ME"

// timing
#define PUBLISH_INTERVAL_S 300                // one reading every 5 minutes
#define WIFI_TIMEOUT_MS    20000
#define BUFFER_SIZE        48                 // offline buffer: 48 readings = 4 h at 5 min
#define MAX_FAILED_CYCLES  12                 // restart the ESP after this many failed uploads in a row

// pins (ESP32 DevKit)
#define PIN_SDA            21
#define PIN_SCL            22
#define PIN_RAIN           27                 // tipping-bucket reed switch to GND (internal pull-up used)
#define PIN_TRIG           5                  // JSN-SR04T trigger
#define PIN_ECHO           18                 // JSN-SR04T echo - MUST go through a 5V->3.3V divider
#define PIN_SOIL           34                 // capacitive soil sensor analog out (ADC1)
#define PIN_BATT           35                 // battery voltage via 100k/100k divider (ADC1)

// rain gauge
#define MM_PER_TIP         0.2794f            // check your gauge datasheet (0.2 mm and 0.5 mm are also common)
#define RAIN_DEBOUNCE_MS   100

// water level (ultrasonic looks DOWN at the water from a fixed bracket)
#define HAS_WATER_SENSOR   1
#define SENSOR_HEIGHT_CM   500.0f             // distance from the sensor face down to the riverbed / drain floor
#define ULTRASONIC_MIN_CM  25.0f              // JSN-SR04T blind zone
#define ULTRASONIC_MAX_CM  450.0f

// soil moisture calibration: read raw ADC in dry air and in a glass of water, then set these
#define SOIL_RAW_DRY       3000
#define SOIL_RAW_WET       1300

// battery divider ratio (100k + 100k -> 2.0)
#define BATT_DIVIDER       2.0f

// BME280 I2C address: 0x76 (SDO to GND) or 0x77
#define BME_ADDR           0x76
