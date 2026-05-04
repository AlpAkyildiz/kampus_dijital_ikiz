import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

BROKER = "broker.hivemq.com"
TOPIC = "dijitalikiz/lab1"

def on_connect(client, userdata, flags, rc):
    print("MQTT Bağlandı")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print("Geldi:", payload)

        data = json.loads(payload)
        turkey_time = datetime.utcnow() + timedelta(hours=3)
        data["created_at"] = turkey_time.isoformat()



        requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_data",
            headers=headers,
            json=data
        )

        print("Supabase kaydedildi")

    except Exception as e:
        print("Hata:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)
client.loop_forever()
