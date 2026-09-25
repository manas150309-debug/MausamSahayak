// MausamSahayak sensor node firmware (Nishant)
//
// Every PUBLISH_INTERVAL_S seconds: read BME280, rain gauge, ultrasonic water level, soil moisture and
// battery; buffer the reading; connect Wi-Fi + MQTT; publish everything buffered; switch radios off;
// light-sleep. Rain tips are counted even while sleeping (GPIO wake-up).
//
// STATUS: written to the ESP32 Arduino core 2.x/3.x APIs but NOT compiled or bench-tested by the
// author of this scaffold. Expect to fix small things on first build and to verify the sleep timing.

#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <Adafruit_BME280.h>
#include <ArduinoJson.h>
#include <time.h>
#include <esp_sleep.h>
#include <esp_timer.h>
#include <driver/gpio.h>
#include "config.h"

// ------------------------------------------------------------------ state
struct Reading {
  uint32_t ts;                 // epoch seconds, 0 if the clock was not synced
  float temp, hum, pres, rain, level, soil, batt;
  int rssi;
};

static Reading buffer_[BUFFER_SIZE];
static int bufCount_ = 0;
static int failedCycles_ = 0;

static WiFiClient wifi_;
static PubSubClient mqtt_(wifi_);
static Adafruit_BME280 bme_;
static bool bmeOk_ = false;

static volatile uint32_t tips_ = 0;
static volatile uint32_t lastTipMs_ = 0;
static portMUX_TYPE tipMux_ = portMUX_INITIALIZER_UNLOCKED;

// ------------------------------------------------------------- rain gauge
static inline void countTip() {
  uint32_t nowMs = (uint32_t)(esp_timer_get_time() / 1000);
  if (nowMs - lastTipMs_ > RAIN_DEBOUNCE_MS) {
    tips_++;
    lastTipMs_ = nowMs;
  }
}

void IRAM_ATTR onTipIsr() {
  portENTER_CRITICAL_ISR(&tipMux_);
  countTip();
  portEXIT_CRITICAL_ISR(&tipMux_);
}

static float takeRainMm() {
  portENTER_CRITICAL(&tipMux_);
  uint32_t t = tips_;
  tips_ = 0;
  portEXIT_CRITICAL(&tipMux_);
  return t * MM_PER_TIP;
}

// ----------------------------------------------------------------- sensors
static float readWaterLevelCm(float airTempC) {
#if HAS_WATER_SENSOR
  float speed = 331.3f + 0.606f * (isnan(airTempC) ? 25.0f : airTempC);   // m/s, temperature compensated
  float s[7];
  int n = 0;
  for (int i = 0; i < 7; i++) {
    digitalWrite(PIN_TRIG, LOW);
    delayMicroseconds(4);
    digitalWrite(PIN_TRIG, HIGH);
    delayMicroseconds(15);
    digitalWrite(PIN_TRIG, LOW);
    unsigned long us = pulseIn(PIN_ECHO, HIGH, 35000UL);
    if (us > 0) s[n++] = us * speed * 5e-5f;   // us * m/s / 2, converted to cm
    delay(70);
  }
  if (n < 3) return NAN;
  for (int i = 1; i < n; i++) {                 // insertion sort, then take the median
    float v = s[i];
    int j = i - 1;
    while (j >= 0 && s[j] > v) { s[j + 1] = s[j]; j--; }
    s[j + 1] = v;
  }
  float dist = s[n / 2];
  if (dist < ULTRASONIC_MIN_CM || dist > ULTRASONIC_MAX_CM) return NAN;
  float level = SENSOR_HEIGHT_CM - dist;
  return level < 0 ? 0 : level;
#else
  return NAN;
#endif
}

static float readSoilPct() {
  uint32_t sum = 0;
  for (int i = 0; i < 16; i++) { sum += analogRead(PIN_SOIL); delay(2); }
  float raw = sum / 16.0f;
  if (raw < 200 || raw > 4000) return NAN;                       // disconnected / shorted
  float pct = (SOIL_RAW_DRY - raw) * 100.0f / (SOIL_RAW_DRY - SOIL_RAW_WET);
  return constrain(pct, 0.0f, 100.0f);
}

static float readBatteryV() {
  uint32_t mv = 0;
  for (int i = 0; i < 8; i++) { mv += analogReadMilliVolts(PIN_BATT); delay(2); }
  return (mv / 8.0f) * BATT_DIVIDER / 1000.0f;
}

static uint32_t epochNow() {
  time_t t = time(nullptr);
  return t > 1700000000 ? (uint32_t)t : 0;
}

static Reading takeReading() {
  Reading r;
  r.temp = r.hum = r.pres = NAN;
  if (bmeOk_ && bme_.takeForcedMeasurement()) {
    r.temp = bme_.readTemperature();
    r.hum = bme_.readHumidity();
    r.pres = bme_.readPressure() / 100.0f;
  }
  r.rain = takeRainMm();
  r.level = readWaterLevelCm(r.temp);
  r.soil = readSoilPct();
  r.batt = readBatteryV();
  r.rssi = 0;
  r.ts = epochNow();
  return r;
}

static void pushReading(const Reading& r) {
  if (bufCount_ == BUFFER_SIZE) {                               // full: drop the oldest
    memmove(buffer_, buffer_ + 1, sizeof(Reading) * (BUFFER_SIZE - 1));
    bufCount_--;
  }
  buffer_[bufCount_++] = r;
}

// ------------------------------------------------------------------ network
static bool connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_TIMEOUT_MS) delay(200);
  if (WiFi.status() != WL_CONNECTED) return false;
  configTime(0, 0, "pool.ntp.org", "time.google.com");           // epoch is UTC
  start = millis();
  while (epochNow() == 0 && millis() - start < 5000) delay(100);
  return true;
}

static bool connectMqtt() {
  mqtt_.setServer(MQTT_HOST, MQTT_PORT);
  mqtt_.setBufferSize(512);
  for (int i = 0; i < 3 && !mqtt_.connected(); i++) {
    if (!mqtt_.connect(NODE_ID, MQTT_USER, MQTT_PASSWORD)) delay(1000);
  }
  return mqtt_.connected();
}

static void setNum(JsonDocument& doc, const char* key, float v, int decimals) {
  if (isnan(v)) { doc[key] = nullptr; return; }
  float m = powf(10.0f, decimals);
  doc[key] = roundf(v * m) / m;
}

static bool publishReading(const Reading& r) {
  JsonDocument doc;
  doc["node_id"] = NODE_ID;
  if (r.ts) doc["ts"] = r.ts;                                    // omitted -> backend stamps receive time
  setNum(doc, "temperature_c", r.temp, 1);
  setNum(doc, "humidity_pct", r.hum, 1);
  setNum(doc, "pressure_hpa", r.pres, 1);
  setNum(doc, "rain_mm", r.rain, 2);
  setNum(doc, "water_level_cm", r.level, 1);
  setNum(doc, "soil_moisture_pct", r.soil, 1);
  setNum(doc, "battery_v", r.batt, 2);
  doc["rssi"] = r.rssi;
  char payload[384];
  size_t n = serializeJson(doc, payload, sizeof(payload));
  char topic[64];
  snprintf(topic, sizeof(topic), "mausam/nodes/%s/telemetry", NODE_ID);
  return n > 0 && mqtt_.publish(topic, (const uint8_t*)payload, n, false);
}

static void uploadBuffered() {
  if (bufCount_ == 0) return;
  if (!connectWifi() || !connectMqtt()) {
    failedCycles_++;
    Serial.printf("upload failed (%d in a row), %d readings buffered\n", failedCycles_, bufCount_);
    if (failedCycles_ >= MAX_FAILED_CYCLES) ESP.restart();
  } else {
    int rssi = WiFi.RSSI();
    int sent = 0;
    while (sent < bufCount_) {
      buffer_[sent].rssi = rssi;
      if (!publishReading(buffer_[sent])) break;
      sent++;
      mqtt_.loop();
      delay(30);
    }
    if (sent > 0) {                                              // drop what was sent, keep the rest
      memmove(buffer_, buffer_ + sent, sizeof(Reading) * (bufCount_ - sent));
      bufCount_ -= sent;
    }
    if (bufCount_ == 0) failedCycles_ = 0; else failedCycles_++;
    delay(100);
    mqtt_.disconnect();
  }
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
}

// -------------------------------------------------------------------- sleep
// Light-sleep until wakeAtUs (esp_timer time). A falling edge on the rain pin wakes us early;
// we count that tip by hand (the ISR is detached during sleep) and go back to sleep.
static void sleepUntil(int64_t wakeAtUs) {
  while (true) {
    int64_t remain = wakeAtUs - esp_timer_get_time();
    if (remain < 500000) break;
    detachInterrupt(digitalPinToInterrupt(PIN_RAIN));
    gpio_wakeup_enable((gpio_num_t)PIN_RAIN, GPIO_INTR_LOW_LEVEL);
    esp_sleep_enable_gpio_wakeup();
    esp_sleep_enable_timer_wakeup((uint64_t)remain);
    esp_light_sleep_start();
    if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_GPIO) {
      portENTER_CRITICAL(&tipMux_);
      countTip();
      portEXIT_CRITICAL(&tipMux_);
      uint32_t t0 = millis();
      while (digitalRead(PIN_RAIN) == LOW && millis() - t0 < 500) delay(5);   // wait for the reed to open
    }
  }
  attachInterrupt(digitalPinToInterrupt(PIN_RAIN), onTipIsr, FALLING);
}

// -------------------------------------------------------------------- setup
void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  bmeOk_ = bme_.begin(BME_ADDR);
  if (bmeOk_) {
    bme_.setSampling(Adafruit_BME280::MODE_FORCED, Adafruit_BME280::SAMPLING_X1,
                     Adafruit_BME280::SAMPLING_X1, Adafruit_BME280::SAMPLING_X1, Adafruit_BME280::FILTER_OFF);
  } else {
    Serial.println("BME280 not found - temperature/humidity will be null (backend will flag UNKNOWN)");
  }
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_RAIN, INPUT_PULLUP);
  analogReadResolution(12);
  attachInterrupt(digitalPinToInterrupt(PIN_RAIN), onTipIsr, FALLING);
  Serial.printf("MausamSahayak node %s starting\n", NODE_ID);
}

void loop() {
  int64_t cycleStart = esp_timer_get_time();
  Reading r = takeReading();
  Serial.printf("T=%.1f H=%.1f P=%.1f rain=%.2f level=%.1f soil=%.1f batt=%.2f\n",
                r.temp, r.hum, r.pres, r.rain, r.level, r.soil, r.batt);
  pushReading(r);
  uploadBuffered();
  sleepUntil(cycleStart + (int64_t)PUBLISH_INTERVAL_S * 1000000LL);
}
