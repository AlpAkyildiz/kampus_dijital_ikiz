from flask import Flask, jsonify, render_template
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/api/live")
def live():

    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/sensor_data?select=*&order=id.desc&limit=1",
        headers=headers
    )

    data = r.json()

    if not data:
        return jsonify({})

    return jsonify(data[0])


@app.route("/api/history")
def history():

    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/sensor_data?select=*&order=created_at.asc&limit=30",
        headers=headers
    )

    return jsonify(r.json())

if __name__ == "__main__":
    app.run(debug=True)
