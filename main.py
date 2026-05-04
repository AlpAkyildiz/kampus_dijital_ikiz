import os
import time
import serial
import requests
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

while True:
    try:
        line = ser.readline().decode("utf-8").strip()

        if not line:
            continue

        print("ESP32:", line)

        temp, hum, gas = line.split(",")

        data = {
            "temperature": float(temp),
            "humidity": float(hum),
            "gas": int(gas),
            "light": 0,
            "current": 0
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_data",
            headers=headers,
            json=data
        )

        print(response.status_code, data)

    except Exception as e:
        print("Hata:", e)

    time.sleep(3)