from flask import Flask, jsonify, request, render_template
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("db.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        value REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return "Sistem çalışıyor"


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


@app.route("/api/add", methods=["POST"])
def add_data():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON veri gelmedi"}), 400

    sensor_type = data.get("type")
    value = data.get("value")

    if sensor_type is None or value is None:
        return jsonify({"error": "Eksik veri"}), 400

    conn = sqlite3.connect("db.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO sensor_data (type, value) VALUES (?, ?)",
        (sensor_type, value)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "type": sensor_type,
        "value": value
    })


@app.route("/api/data")
def get_data():
    conn = sqlite3.connect("db.db")
    c = conn.cursor()

    c.execute("SELECT value FROM sensor_data WHERE type='temperature' ORDER BY id DESC LIMIT 1")
    temp_row = c.fetchone()

    c.execute("SELECT value FROM sensor_data WHERE type='humidity' ORDER BY id DESC LIMIT 1")
    hum_row = c.fetchone()

    c.execute("SELECT value FROM sensor_data WHERE type='light' ORDER BY id DESC LIMIT 1")
    light_row = c.fetchone()

    conn.close()

    return jsonify({
        "temperature": temp_row[0] if temp_row else 0,
        "humidity": hum_row[0] if hum_row else 0,
        "light": light_row[0] if light_row else 0
    })


if __name__ == "__main__":
    app.run(debug=True)