# Kampüs Enerji Dijital İkizi

Bu proje, IoT tabanlı bir dijital ikiz sistemi kullanarak kampüs ortamındaki enerji tüketimini izlemek ve kontrol etmek amacıyla geliştirilmiştir.

## 🚀 Proje Amacı
- Sensör verilerini (sıcaklık, ışık vb.) toplamak
- Verileri gerçek zamanlı olarak izlemek
- Web arayüzü üzerinden cihaz kontrolü sağlamak
- Enerji tüketimini analiz etmek

## 🧩 Kullanılan Teknolojiler
- Python (Flask)
- SQLite
- MQTT
- HTML / CSS / JavaScript
- ESP32 / Arduino

## 🔄 Sistem Mimarisi
Sensör → ESP32 → MQTT → Flask → Veritabanı → Web Arayüzü

## 👥 Proje Ekibi
- Alperen Akyıldız → Backend & Arayüz
- Esma Mol → IoT & Donanım

## ⚙️ Kurulum

```bash
pip install flask paho-mqtt
python app.py
