from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Sistem çalışıyor 🚀"

print("Dosya çalıştı")  # bunu ekledik test için

if __name__ == "__main__":
    app.run(debug=True)
