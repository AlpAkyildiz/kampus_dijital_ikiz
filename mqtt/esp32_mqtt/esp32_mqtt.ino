#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define MQTT_MAX_PACKET_SIZE 512

#define DHTPIN 4
#define DHTTYPE DHT11

#define GAS_PIN 34
#define ALARM_PIN 27
#define CURRENT_PIN 32
#define PIR_PIN 25

#define LED_PIN 5

#define LIGHT_PIN 35
#define FLAME_A0 33

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Xiaomi 14T Pro";
const char* password = "Swedrf234";

const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

bool ledState = false;

// Callback bildirimi
void callback(char* topic, byte* payload, unsigned int length);

// ACS712
float sensitivity = 0.066;
float zeroCurrentVoltage = 2.410;

void setup_wifi() {

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi bağlandı");
}

void reconnect() {

  while (!client.connected()) {

    Serial.println("MQTT bağlanıyor...");

    if (client.connect("ESP32Client123")) {

      Serial.println("✅ MQTT bağlandı");

      client.subscribe("dijitalikiz/lab1/led");

    } else {

      Serial.println("❌ MQTT bağlanamadı...");
      delay(2000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {

  String msg = "";

  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  Serial.print("MQTT Mesajı: ");
  Serial.println(msg);

  if (msg == "ON") {
    ledState = true;
    digitalWrite(LED_PIN, HIGH);
    Serial.println("💡 LED AÇILDI");
  }

  else if (msg == "OFF") {
    ledState = false;
    digitalWrite(LED_PIN, LOW);
    Serial.println("💡 LED KAPATILDI");
  }
}

float readCurrent() {

  long total = 0;

  for (int i = 0; i < 50; i++) {
    total += analogRead(CURRENT_PIN);
    delay(2);
  }

  int raw = total / 50;

  float voltage = (raw / 4095.0) * 3.3;
  float current = (voltage - zeroCurrentVoltage) / sensitivity;

  if (current < 0.15 && current > -0.15)
    current = 0;

  return abs(current);
}

void setup() {

  Serial.begin(115200);

  dht.begin();

  pinMode(ALARM_PIN, INPUT_PULLUP);
  pinMode(PIR_PIN, INPUT);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  analogReadResolution(12);

  setup_wifi();

  client.setServer(mqtt_server, 1883);
  client.setBufferSize(512);
  client.setCallback(callback);
}

void loop() {

  if (!client.connected())
    reconnect();

  client.loop();

  int motion = digitalRead(PIR_PIN);
  bool motionDetected = (motion == HIGH);

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  if (isnan(temp) || isnan(hum)) {
    temp = 0;
    hum = 0;
  }

  int gas = analogRead(GAS_PIN);
  int alarm = digitalRead(ALARM_PIN);

  float current = readCurrent();

  // Işık
  int lightValue = analogRead(LIGHT_PIN);
  bool lightDetected = (lightValue < 2000);
  digitalWrite(LED_PIN, ledState ? HIGH : LOW);

  // Alev
  int flameValue = analogRead(FLAME_A0);
  bool flameDetected = (flameValue < 2000);

  Serial.print("Light: ");
  Serial.print(lightValue);

  Serial.print(" | Flame: ");
  Serial.print(flameValue);

  Serial.print(" | Current: ");
  Serial.print(current);

  Serial.print(" | Motion: ");
  Serial.println(motionDetected);

  String payload = "{";

  payload += "\"temperature\":" + String(temp, 1) + ",";
  payload += "\"humidity\":" + String(hum, 1) + ",";
  payload += "\"gas\":" + String(gas) + ",";
  payload += "\"gas_alarm\":" + String(alarm == 0 ? "true" : "false") + ",";

  payload += "\"light_detected\":" + String(lightDetected ? "true" : "false") + ",";
  payload += "\"light_value\":" + String(lightValue) + ",";

  payload += "\"flame_detected\":" + String(flameDetected ? "true" : "false") + ",";
  payload += "\"flame_value\":" + String(flameValue) + ",";

  payload += "\"current\":" + String(current, 2) + ",";
  payload += "\"motion_detected\":" + String(motionDetected ? "true" : "false");

  payload += "}";

  if (client.publish("dijitalikiz/lab1", payload.c_str())) {
    Serial.println("✅ GÖNDERİLDİ");
  } else {
    Serial.println("❌ GÖNDERİLEMEDİ");
  }

  Serial.println(payload);

  delay(3000);
}