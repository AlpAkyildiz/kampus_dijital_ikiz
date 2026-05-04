#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define GAS_PIN 34
#define ALARM_PIN 27

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Xiaomi 14T Pro";
const char* password = "Swedrf234";

const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

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

void setup() {
  Serial.begin(115200);

  dht.begin();

  pinMode(ALARM_PIN, INPUT);

  setup_wifi();

  client.setServer(mqtt_server, 1883);
}

void loop() {

  if (!client.connected()) reconnect();

  client.loop();

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  int gas = analogRead(GAS_PIN);
  int alarm = digitalRead(ALARM_PIN);

  String payload = "{";
  payload += "\"temperature\":" + String(temp,1) + ",";
  payload += "\"humidity\":" + String(hum,1) + ",";
  payload += "\"gas\":" + String(gas) + ",";
  payload += "\"gas_alarm\":" + String(alarm == 0 ? "true":"false") + ",";
  payload += "\"light\":0,";
  payload += "\"current\":0";
  payload += "}";

  client.publish("dijitalikiz/lab1", payload.c_str());

  Serial.println(payload);

  delay(3000);
}
