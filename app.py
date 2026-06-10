import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import paho.mqtt.publish as publish
from datetime import datetime, timedelta

print("🚀 APP.PY BAŞLADI")





LIGHT_THRESHOLD = 500


light_state = False

# 🔥 Firebase Admin
import firebase_admin
from firebase_admin import credentials, messaging

load_dotenv()

app = Flask(__name__)
CORS(app)

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "dijitalikiz/lab1/led"

# 🔑 Firebase Admin init (ENV'den)
cred_json = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(cred_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# 🌍 ENV
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")





headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}



# 📲 TOKEN KAYDET
@app.route("/api/token", methods=["POST"])
def save_token():
    data = request.json
    token = data.get("token")

    if token:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/fcm_tokens",
            headers={
                **headers,
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            json={
                "token": token
            }
        )

    return {"status": "ok"}








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
    print("🌐 LIVE ÇAĞRILDI", flush=True)


    data = r.json()

    if not data:
        return jsonify({})

    sensor = data[0]

    

    return jsonify(sensor)


@app.route("/api/events")
def events():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/notification_logs?select=*&order=created_at.desc&limit=30",
        headers=headers
    )

    return jsonify(r.json())



@app.route("/api/light/on", methods=["POST"])
def light_on():
    global light_state

    light_state = True

    publish.single(
        MQTT_TOPIC,
        "ON",
        hostname=MQTT_BROKER
    )

    return {
        "status": "ok",
        "light": light_state
    }


@app.route("/api/light/off", methods=["POST"])
def light_off():
    global light_state

    light_state = False

    publish.single(
        MQTT_TOPIC,
        "OFF",
        hostname=MQTT_BROKER
    )

    return {
        "status": "ok",
        "light": light_state
    }

@app.route("/api/light/status")
def light_status():
    return {
        "light": light_state
    }

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