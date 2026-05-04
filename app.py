from flask import Flask, jsonify, request, render_template
import sqlite3
import random
import threading
import time

app = Flask(__name__)
DB_NAME = "db.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

#  DB
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT,
            device_name TEXT,
            status TEXT DEFAULT 'on',
            power REAL,
            UNIQUE(room, device_name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_energy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT,
            device TEXT,
            value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

init_db()

#  SİMÜLASYON
def simulate_device(room, device, power):
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status FROM room_devices
            WHERE room=? AND device_name=?
        """, (room, device))

        row = cursor.fetchone()
        status = row["status"] if row else "off"

        if status == "off":
            value = 0
        else:
            if device == "light":
                value = power
            elif device == "projector":
                value = power * random.uniform(0.9, 1.1)
            elif device == "computers":
                value = power * random.uniform(0.5, 1.5)
            elif device == "sockets":
                value = power * random.uniform(0.2, 2.0)
            else:
                value = power

        cursor.execute("""
            INSERT INTO device_energy_log (room, device, value)
            VALUES (?, ?, ?)
        """, (room, device, value))

        conn.commit()
        conn.close()

        time.sleep(5)

#  TÜM CİHAZLARI BAŞLAT
def start_all_devices():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT room, device_name, power FROM room_devices")
    devices = cursor.fetchall()
    conn.close()

    for d in devices:
        t = threading.Thread(
            target=simulate_device,
            args=(d["room"], d["device_name"], d["power"]),
            daemon=True
        )
        t.start()

start_all_devices()

#  SAYFALAR
@app.route("/")
def home():
    return "Sistem çalışıyor"

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/room")
def room_page():
    room = request.args.get("room")
    return render_template("room.html", room=room)

@app.route("/api/add-room", methods=["POST"])
def add_room():

    data = request.get_json()
    room = data.get("room")
    devices = data.get("devices")

    if not room or not devices:
        return jsonify({"error": "room ve devices gerekli"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    for d in devices:
    
      cursor.execute("""
        INSERT INTO room_devices (room, device_name, power)
        VALUES (?, ?, ?)
      """, (room, d["name"], d["power"]))

    #  chart için ilk veri
    cursor.execute("""
        INSERT INTO device_energy_log (room, device, value)
        VALUES (?, ?, 0)
    """, (room, d["name"]))

    #  simülasyon başlat
    t = threading.Thread(
        target=simulate_device,
        args=(room, d["name"], d["power"]),
        daemon=True
    )
    t.start()


    conn.commit()
    conn.close()

    return jsonify({"status": "oda oluşturuldu"})

@app.route("/api/room/<room>/device-history")
def device_history(room):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT device, value, timestamp
        FROM device_energy_log
        WHERE room=?
        ORDER BY timestamp ASC
    """, (room,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/api/delete-room", methods=["DELETE"])
def delete_room():

    data = request.get_json()
    room = data.get("room")

    if not room:
        return jsonify({"error": "room gerekli"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    #  oda cihazlarını sil
    cursor.execute("DELETE FROM room_devices WHERE room=?", (room,))

    #  enerji loglarını da sil
    cursor.execute("DELETE FROM device_energy_log WHERE room=?", (room,))

    conn.commit()
    conn.close()

    return jsonify({"status": "oda silindi"})


#  CİHAZ KONTROL
@app.route("/api/room/control", methods=["POST"])
def control_room():
    data = request.get_json()

    room = data.get("room")
    device = data.get("device")
    status = data.get("status")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE room_devices
        SET status=?
        WHERE room=? AND device_name=?
    """, (status, room, device))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

#  ODA CİHAZLARI
@app.route("/api/room/<room>/devices")
def get_room_devices(room):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT device_name, power, status
        FROM room_devices
        WHERE room=?
    """, (room,))

    devices = cursor.fetchall()

    result = []
    total = 0

    for d in devices:
        energy = d["power"] if d["status"] == "on" else 0
        total += energy

        result.append({
            "device": d["device_name"],
            "status": d["status"],
            "power": d["power"],
            "energy": energy
        })

    conn.close()

    return jsonify({
        "room": room,
        "devices": result,
        "total_energy": round(total, 2)
    })

#  SUMMARY 
@app.route("/api/summary")
def summary():

    conn = get_db_connection()
    cursor = conn.cursor()

    #  TÜM ODALAR 
    cursor.execute("SELECT DISTINCT room FROM room_devices")
    rooms = [r["room"] for r in cursor.fetchall()]

    room_usage = {}
    total_energy = 0

    for room in rooms:
        cursor.execute("""
            SELECT SUM(value) as total
            FROM device_energy_log
            WHERE room=?
        """, (room,))

        total = cursor.fetchone()["total"] or 0

        room_usage[room] = total
        total_energy += total

    conn.close()

    most_used_room = max(room_usage, key=room_usage.get) if room_usage else None

    return jsonify({
        "total_energy": round(total_energy, 2),
        "most_used_room": most_used_room,
        "room_usage": room_usage
    })

#  LINE CHART DATA
@app.route("/api/data")
def get_all_data():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT room, value, timestamp
        FROM device_energy_log
        ORDER BY timestamp ASC
        LIMIT 1000
    """)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "room": r["room"],
            "value": r["value"],
            "timestamp": r["timestamp"],
            "type": "energy"
        }
        for r in rows
    ])

#  TEMİZLE
@app.route("/api/clear", methods=["DELETE"])
def clear():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM device_energy_log")

    conn.commit()
    conn.close()

    return jsonify({"status": "temizlendi"})

if __name__ == "__main__":
    app.run(debug=True)
