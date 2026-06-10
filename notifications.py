import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, messaging

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

cred_json = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

last_motion_time = datetime.now()
light_alert_sent = False

LIGHT_THRESHOLD = 500

last_state = {
    "gas_alert": False,
    "flame_alert": False
}


def send_push(title, body):
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/fcm_tokens?select=token",
            headers=headers
        )

        tokens = r.json()

        for row in tokens:
            token = row["token"]

            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    token=token,
                )

                response = messaging.send(message)
                print("✅ Push:", response)

            except Exception as e:
                print("❌ Push hatası:", e)

    except Exception as e:
        print("❌ Token çekme hatası:", e)


def save_event(event_type, message, value=None):
    requests.post(
        f"{SUPABASE_URL}/rest/v1/notification_logs",
        headers={
            **headers,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json={
            "type": event_type,
            "message": message,
            "sensor_value": value
        }
    )


def check_and_notify(sensor):
    global last_motion_time
    global light_alert_sent

    gas = sensor.get("gas", 0)
    flame = sensor.get("flame_detected", False)
    motion = sensor.get("motion_detected", False)
    light_value = sensor.get("light_value", 0)
    light_detected = sensor.get("light_detected", False)

    if gas > 2000:
        if not last_state["gas_alert"]:
            send_push("🚨 Gaz Tehlikesi!", f"Değer: {gas}")
            save_event("gas", "Gaz seviyesi kritik", gas)
            last_state["gas_alert"] = True
    else:
        last_state["gas_alert"] = False

    if motion:
        last_motion_time = datetime.now()

    if flame:
        if not last_state["flame_alert"]:
            send_push("🔥 Alev Algılandı!", "Acil kontrol gerekli!")
            save_event("flame", "Alev algılandı")
            last_state["flame_alert"] = True
    else:
        last_state["flame_alert"] = False

    inactive = (
        datetime.now() - last_motion_time
    ) > timedelta(seconds=15)

    light_on = (
        light_detected or
        light_value > LIGHT_THRESHOLD
    )

    if inactive and light_on:
        if not light_alert_sent:
            send_push(
                "💡 Işıklar Açık Kalmış",
                "LAB 1 sınıfında uzun süredir hareket yok ancak ışıklar açık görünüyor."
            )
            save_event("light", "Işık açık kaldı")
            light_alert_sent = True
    else:
        light_alert_sent = False