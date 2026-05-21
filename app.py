import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS").split(",")

last_alert_time = 0

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def send_telegram(msg):
    global last_alert_time

    now = time.time()

    # 60 saniyede bir uyarı göndersin, spam olmasın
    if now - last_alert_time < 60:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    try:
        requests.post(url, data=data)
        last_alert_time = now
        print("Telegram bildirimi gönderildi")
    except Exception as e:
        print("Telegram gönderilemedi:", e)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


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

    gas = sensor.get("gas", 0)
    flame = sensor.get("flame_detected", False)

    if gas > 2000:
        send_telegram(f"🔥 UYARI! Gaz seviyesi yüksek: {gas}")

    if flame == True:
        send_telegram("🔥 UYARI! Alev algılandı!")

    return jsonify(sensor)


@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")


@app.route("/api/history")
def history():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/sensor_data?select=*&order=id.asc&limit=30",
        headers=headers
    )
    return jsonify(r.json())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)