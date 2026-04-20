from flask import Flask, render_template
import os

app = Flask(__name__)

# Sample Data for Aramedica Farma
CATEGORIES = {
    "Vitamin & Suplemen": [
        {"name": "Vitamin C 1000mg", "price": "Rp 45.000", "desc": "Menjaga daya tahan tubuh tetap optimal."},
        {"name": "Omega 3 Fish Oil", "price": "Rp 85.000", "desc": "Kesehatan jantung dan fungsi otak."},
        {"name": "Multivitamin Zink", "price": "Rp 30.000", "desc": "Suplemen harian untuk energi dan imun."},
    ],
    "Obat Umum (OTC)": [
        {"name": "Paracetamol 500mg", "price": "Rp 10.000", "desc": "Meredakan demam dan sakit kepala."},
        {"name": "Obat Batuk Sirup", "price": "Rp 25.000", "desc": "Meredakan batuk berdahak dan tenggorokan gatal."},
        {"name": "Antasida Doen", "price": "Rp 15.000", "desc": "Mengatasi asam lambung dan maag."},
    ],
    "Kesehatan Kulit & Kecantikan": [
        {"name": " Krim Anti-Acne", "price": "Rp 55.000", "desc": "Mengatasi jerawat dan bekas jerawat."},
        {"name": "Moisturizer Hydrating", "price": "Rp 75.000", "desc": "Melembabkan kulit kering dan sensitif."},
    ]
}

@app.route('/')
def home():
    return render_template('index.html', categories=CATEGORIES)

if __name__ == '__main__':
    # Run on 0.0.0.0 and port 5001 to avoid conflict with MokiDonut
    app.run(host='0.0.0.0', port=5001)
