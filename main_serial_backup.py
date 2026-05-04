import os
import time
import serial
import requests
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
COM_PORT = os.getenv("COM_PORT")

ser = serial.Serial(COM_PORT, 115200, timeout=1)

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

time.sleep(3)

while True:
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if not line:
            continue

        print("ESP32:", line)

        if line.count(",") != 3:
            continue

        temp, hum, gas, alarm = line.split(",")

        turkey_time = datetime.utcnow() + timedelta(hours=3);

        data = {
            "temperature": float(temp),
            "humidity": float(hum),
            "gas": int(gas),
            "gas_alarm": int(alarm) == 0,
            "light": 0,
            "current": 0,
            "created_at": turkey_time.isoformat()
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_data",
            headers=headers,
            json=data
        )

        print(response.status_code)
        print(data)

    except Exception as e:
        print("Hata:", e)

    time.sleep(3)
