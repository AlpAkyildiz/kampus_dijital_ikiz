import json
import requests
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv

# 🔥 .env yükle
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

# 🔍 debug (çok önemli)
print("URL:", SUPABASE_URL)
print("KEY:", "OK" if KEY else "YOK")

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

BROKER = "broker.hivemq.com"
TOPIC = "dijitalikiz/lab1"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Bağlandı")
        client.subscribe(TOPIC)
    else:
        print("❌ MQTT Hata kodu:", rc)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print("📩 Veri geldi:", payload)

        data = json.loads(payload)

        # 🔥 garanti alanlar
        data.setdefault("temperature", 0)
        data.setdefault("humidity", 0)
        data.setdefault("gas", 0)
        data.setdefault("gas_alarm", False)
        data.setdefault("light_detected", False)
        data.setdefault("flame_detected", False)
        data.setdefault("flame_value", 0)
        data.setdefault("current", 0)
        data.setdefault("motion_detected", False)

        # 🕒 Türkiye saat
        turkey_time = datetime.utcnow() + timedelta(hours=3)
        data["created_at"] = turkey_time.strftime("%Y-%m-%d %H:%M:%S")

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_data",
            headers=headers,
            json=data
        )

        print("STATUS:", response.status_code)

        if response.status_code in [200, 201]:
            print("✅ Supabase kaydedildi")
        else:
            print("❌ DB hata:", response.text)

    except Exception as e:
        print("❌ Hata:", e)


# 🔥 client oluştur
client = mqtt.Client(client_id="esp32_subscriber_v2")

client.on_connect = on_connect
client.on_message = on_message

print("🚀 MQTT bağlanıyor...")

try:
    client.connect(BROKER, 1883, 60)
except Exception as e:
    print("❌ Broker bağlantı hatası:", e)

client.loop_forever()