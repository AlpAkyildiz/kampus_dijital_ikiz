from flask import Flask, jsonify, request, render_template
import sqlite3

app = Flask(__name__)
DB_NAME = "db.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# 🔥 DB KURULUM
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # sensör verisi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            type TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # oda cihazları
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT,
            device_name TEXT,
            status TEXT DEFAULT 'off',
            power REAL DEFAULT 0,
            UNIQUE(room, device_name)
        )
    """)

    # örnek cihazlar (ilk çalıştırmada eklenir)
    devices = [
        ("lab_403", "light", 0.5),
        ("lab_403", "projector", 1.2),
        ("lab_403", "computers", 3.5),
        ("lab_403", "sockets", 2.0),

        ("sinif_414", "light", 0.4),
        ("sinif_414", "projector", 1.0),
        ("sinif_414", "sockets", 1.5),

        ("koridor", "light", 0.3)
    ]

    for room, device, power in devices:
        cursor.execute("""
            INSERT OR IGNORE INTO room_devices (room, device_name, power)
            VALUES (?, ?, ?)
        """, (room, device, power))

    conn.commit()
    conn.close()

init_db()

# 🔷 SAYFALAR
@app.route("/")
def home():
    return "Sistem çalışıyor"

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")



# 🔷 VERİ EKLE
@app.route("/api/add", methods=["POST"])
def add_data():
    data = request.get_json()

    room = data.get("room")
    sensor_type = data.get("type")
    value = data.get("value")

    if not room or not sensor_type or value is None:
        return jsonify({"error": "Eksik veri"}), 400

    valid_types = ["temperature", "light", "energy"]

    if sensor_type not in valid_types:
        return jsonify({"error": "Geçersiz type"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sensor_data (room, type, value)
        VALUES (?, ?, ?)
    """, (room, sensor_type, value))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# 🔷 TÜM VERİLER
@app.route("/api/data")
def get_all_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

# 🔷 ODA VERİSİ (grafik için)
@app.route("/api/room/<room>/data")
def get_room_data(room):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT type, value, timestamp
        FROM sensor_data
        WHERE room = ?
        ORDER BY id DESC
    """, (room,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

# 🔷 ODA CİHAZLARI
@app.route("/api/room/<room>/devices")
def get_room_devices(room):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT device_name, status, power
        FROM room_devices
        WHERE room = ?
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
        "total_energy": total
    })

# 🔷 CİHAZ KONTROL
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
        SET status = ?
        WHERE room = ? AND device_name = ?
    """, (status, room, device))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# 🔷 GENEL ÖZET
@app.route("/api/summary")
def summary():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT room, SUM(value) as total
        FROM sensor_data
        WHERE type='energy'
        GROUP BY room
    """)

    rows = cursor.fetchall()

    total_energy = 0
    room_usage = {}

    for row in rows:
        room_usage[row["room"]] = row["total"]
        total_energy += row["total"]

    conn.close()

    most_used_room = max(room_usage, key=room_usage.get) if room_usage else None

    return jsonify({
        "total_energy": round(total_energy, 2),
        "most_used_room": most_used_room,
        "room_usage": room_usage
    })

@app.route("/room")
def room_page():
    room = request.args.get("room")
    return render_template("room.html", room=room)


# 🔷 TEMİZLE
@app.route("/api/clear", methods=["DELETE"])
def clear():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sensor_data")

    conn.commit()
    conn.close()

    return jsonify({"status": "temizlendi"})

if __name__ == "__main__":
    app.run(debug=True)
