import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json

from datetime import datetime, timedelta

last_motion_time = datetime.now()

light_alert_sent = False

LIGHT_THRESHOLD = 500




# 🔥 Firebase Admin
import firebase_admin
from firebase_admin import credentials, messaging

load_dotenv()

app = Flask(__name__)
CORS(app)

# 🔑 Firebase Admin init (ENV'den)
cred_json = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# 🌍 ENV
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 📱 token list (geçici)
tokens = set()

# 🧠 state
last_state = {
    "gas_alert": False,
    "flame_alert": False
}

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# 📲 PUSH
def send_push(title, body):
    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=token,
            )

            messaging.send(message)
            print("✅ Push gönderildi")

        except Exception as e:
            print("❌ Push hatası:", e)

# 📲 TOKEN KAYDET
@app.route("/api/token", methods=["POST"])
def save_token():
    data = request.json
    token = data.get("token")

    if token:
        tokens.add(token)
        print("📱 Token kaydedildi:", token)

    return {"status": "ok"}

# 🧠 AKILLI KONTROL
def check_and_notify(sensor):
    global last_motion_time
    global light_alert_sent

    gas = sensor.get("gas", 0)
    flame = sensor.get("flame_detected", False)
    motion = sensor.get("motion_detected", False)
    light_value = sensor.get("light", 0)  # eğer sayı olarak geliyorsa
    light_detected = sensor.get("light_detected", False)

    # 🚨 GAZ
    if gas > 2000:
        if not last_state["gas_alert"]:
            send_push("🚨 Gaz Tehlikesi!", f"Değer: {gas}")
            last_state["gas_alert"] = True
    else:
        last_state["gas_alert"] = False

    # 🚶 HAREKET
    if motion:
        last_motion_time = datetime.now()

    # 🔥 ALEV
    if flame:
        if not last_state["flame_alert"]:
            send_push("🔥 Alev Algılandı!", "Acil kontrol gerekli!")
            last_state["flame_alert"] = True
    else:
        last_state["flame_alert"] = False

    # 💡 IŞIK KONTROLÜ

    inactive = (
        datetime.now() - last_motion_time
    ) > timedelta(minutes=1)  # test için

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

            print("💡 LAB 1 ışık uyarısı gönderildi")

            light_alert_sent = True

    else:
        light_alert_sent = False

# 🌐 SAYFALAR
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

# 📡 CANLI DATA
@app.route("/api/live")
def live():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/sensor_data?select=*&order=created_at.desc&limit=1",
        headers=headers
    )

    data = r.json()

    if not data:
        return jsonify({})

    sensor = data[0]

    # 🔥 AKILLI BİLDİRİM
    check_and_notify(sensor)

    return jsonify(sensor)

# 📊 GEÇMİŞ
@app.route("/api/history")
def history():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/sensor_data?select=*&order=id.asc&limit=30",
        headers=headers
    )
    return jsonify(r.json())

@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)