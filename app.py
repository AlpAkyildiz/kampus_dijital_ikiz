from flask import Flask, jsonify, request, render_template
import sqlite3

app = Flask(__name__)
DB_NAME = "db.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'off',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS control_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    for device in ["lighting", "fan", "hvac"]:
        cursor.execute("""
            INSERT OR IGNORE INTO device_status (device_name, status)
            VALUES (?, 'off')
        """, (device,))

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return "Kampus Enerji Dijital Ikizi sistemi calisiyor."


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

    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        return jsonify({"error": "Gecersiz sensor tipi"}), 400

    try:
        value = float(value)
    except (ValueError, TypeError):
        return jsonify({"error": "Value sayisal olmali"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sensor_data (type, value)
        VALUES (?, ?)
    """, (sensor_type, value))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "id": new_id,
        "type": sensor_type,
        "value": value
    }), 201


@app.route("/api/data", methods=["GET"])
def get_latest_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    result = {}

    for sensor_type in ["temperature", "humidity", "light"]:
        cursor.execute("""
            SELECT value, timestamp
            FROM sensor_data
            WHERE type = ?
            ORDER BY id DESC
            LIMIT 1
        """, (sensor_type,))
        row = cursor.fetchone()

        if row:
            result[sensor_type] = row["value"]
            result[f"{sensor_type}_timestamp"] = row["timestamp"]
        else:
            result[sensor_type] = 0
            result[f"{sensor_type}_timestamp"] = None

    conn.close()
    return jsonify(result)


@app.route("/api/history/<sensor_type>", methods=["GET"])
def get_sensor_history(sensor_type):
    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        return jsonify({"error": "Gecersiz sensor tipi"}), 400

    limit = request.args.get("limit", default=12, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, value, timestamp
        FROM sensor_data
        WHERE type = ?
        ORDER BY id DESC
        LIMIT ?
    """, (sensor_type, limit))

    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in reversed(rows):
        data.append({
            "id": row["id"],
            "type": row["type"],
            "value": row["value"],
            "timestamp": row["timestamp"]
        })

    return jsonify(data)


@app.route("/api/all", methods=["GET"])
def get_all_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, value, timestamp
        FROM sensor_data
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "id": row["id"],
            "type": row["type"],
            "value": row["value"],
            "timestamp": row["timestamp"]
        })

    return jsonify(data)


@app.route("/api/summary", methods=["GET"])
def get_summary():
    conn = get_db_connection()
    cursor = conn.cursor()

    latest = {}
    for sensor_type in ["temperature", "humidity", "light"]:
        cursor.execute("""
            SELECT value
            FROM sensor_data
            WHERE type = ?
            ORDER BY id DESC
            LIMIT 1
        """, (sensor_type,))
        row = cursor.fetchone()
        latest[sensor_type] = row["value"] if row else 0

    cursor.execute("""
        SELECT COUNT(*) as count
        FROM device_status
        WHERE status = 'on'
    """)
    active_devices = cursor.fetchone()["count"]

    temperature = latest["temperature"]
    humidity = latest["humidity"]
    light = latest["light"]

    total_energy = round((light * 0.18) + (temperature * 1.4) + (humidity * 0.65), 2)
    current_load = round((temperature * 0.9) + (light * 0.05), 2)
    estimated_saving = round(max(0, 8000 - total_energy * 4.2), 2)

    conn.close()

    return jsonify({
        "total_energy": total_energy,
        "active_devices": active_devices,
        "avg_temperature": round(temperature, 2),
        "current_load": current_load,
        "estimated_saving": estimated_saving
    })


@app.route("/api/devices", methods=["GET"])
def get_devices():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT device_name, status, updated_at
        FROM device_status
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    devices = []
    for row in rows:
        devices.append({
            "device_name": row["device_name"],
            "status": row["status"],
            "updated_at": row["updated_at"]
        })

    return jsonify(devices)


@app.route("/api/control", methods=["POST"])
def control_device():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON veri gelmedi"}), 400

    device_name = data.get("device")
    status = data.get("status")

    valid_devices = ["lighting", "fan", "hvac"]
    valid_status = ["on", "off"]

    if device_name not in valid_devices:
        return jsonify({"error": "Gecersiz cihaz"}), 400

    if status not in valid_status:
        return jsonify({"error": "Gecersiz durum"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE device_status
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE device_name = ?
    """, (status, device_name))

    cursor.execute("""
        INSERT INTO control_logs (device_name, status)
        VALUES (?, ?)
    """, (device_name, status))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "device": device_name,
        "new_status": status
    })


@app.route("/api/simulate", methods=["POST"])
def simulate_scenario():
    data = request.get_json()
    scenario = data.get("scenario")

    scenarios = {
        "normal": {
            "temperature": 24.5,
            "humidity": 48,
            "light": 420
        },
        "busy": {
            "temperature": 31.2,
            "humidity": 58,
            "light": 650
        },
        "night": {
            "temperature": 21.3,
            "humidity": 52,
            "light": 140
        }
    }

    if scenario not in scenarios:
        return jsonify({"error": "Gecersiz senaryo"}), 400

    values = scenarios[scenario]

    conn = get_db_connection()
    cursor = conn.cursor()

    for sensor_type, value in values.items():
        cursor.execute("""
            INSERT INTO sensor_data (type, value)
            VALUES (?, ?)
        """, (sensor_type, value))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "scenario": scenario,
        "values": values
    })


@app.route("/api/clear", methods=["DELETE"])
def clear_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sensor_data")
    cursor.execute("DELETE FROM control_logs")

    cursor.execute("""
        UPDATE device_status
        SET status = 'off', updated_at = CURRENT_TIMESTAMP
    """)

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "message": "Tum test verileri temizlendi"
    })


if __name__ == "__main__":
    app.run(debug=True)