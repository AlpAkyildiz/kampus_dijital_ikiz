#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11

#define GAS_PIN 34
#define ALARM_PIN 27
#define CURRENT_PIN 32

#define LIGHT_PIN 25       // Işık sensörü D0
#define FLAME_D0 26        // Alev sensörü D0
#define FLAME_A0 33        // Alev sensörü A0

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Xiaomi 14T Pro";
const char* password = "Swedrf234";

const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

// ACS712 30A ayarları
float sensitivity = 0.066;
float zeroCurrentVoltage = 2.5;

void setup_wifi() {

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("WiFi bağlandı");
}

void reconnect() {

  while (!client.connected()) {

    if (client.connect("ESP32Client123")) {
      Serial.println("MQTT bağlandı");
    } else {
      delay(2000);
    }
  }
}

float readCurrent() {

  long total = 0;

  for(int i=0; i<20; i++){
    total += analogRead(CURRENT_PIN);
    delay(2);
  }

  int raw = total / 20;

  float voltage = (raw / 4095.0) * 3.3;

  float zeroScaled = zeroCurrentVoltage * (3.3 / 5.0);

  float current = (voltage - zeroScaled) / sensitivity;

  if(current < 0.08 && current > -0.08)
    current = 0;

  return abs(current);
}

void setup() {

  Serial.begin(115200);

  dht.begin();

  pinMode(ALARM_PIN, INPUT_PULLUP);
  pinMode(LIGHT_PIN, INPUT);
  pinMode(FLAME_D0, INPUT);

  analogReadResolution(12);

  setup_wifi();

  client.setServer(mqtt_server, 1883);
}

void loop() {

  if (!client.connected())
    reconnect();

  client.loop();

  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  if (isnan(temp) || isnan(hum)) {
    temp = 0;
    hum = 0;
  }

  int gas = analogRead(GAS_PIN);
  int alarm = digitalRead(ALARM_PIN);

  float current = readCurrent();

  int lightState = digitalRead(LIGHT_PIN);

  int flameState = digitalRead(FLAME_D0);
  int flameValue = analogRead(FLAME_A0);

  String payload = "{";

  payload += "\"temperature\":" + String(temp,1) + ",";
  payload += "\"humidity\":" + String(hum,1) + ",";
  payload += "\"gas\":" + String(gas) + ",";
  payload += "\"gas_alarm\":" + String(alarm == 0 ? "true":"false") + ",";

  payload += "\"light_detected\":" + String(lightState == 0 ? "true":"false") + ",";

  payload += "\"flame_detected\":" + String(flameState == 0 ? "true":"false") + ",";
  payload += "\"flame_value\":" + String(flameValue) + ",";

  payload += "\"current\":" + String(current,2);

  payload += "}";

  client.publish("dijitalikiz/lab1", payload.c_str());

  Serial.println(payload);

  delay(3000);
}