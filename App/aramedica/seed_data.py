import sqlite3
from datetime import datetime, timedelta

DB_PATH = '/root/.openclaw/workspace/App/aramedica/pharmacy.db'

def init_dummy_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Dummy Patients
    patients = [
        ('Budi Santoso', '08123456789', 'Jl. Mawar No. 10', 'Alergi Penicillin'),
        ('Siti Aminah', '08567890123', 'Jl. Melati No. 5', 'Hipertensi'),
        ('Andi Wijaya', '08781234567', 'Jl. Kenanga No. 2', 'Diabetes Type 2'),
        ('Dewi Sartika', '08112233445', 'Jl. Anggrek No. 8', 'Tidak ada alergi'),
    ]
    cursor.executemany("INSERT INTO patients (name, phone, address, medical_history) VALUES (?, ?, ?, ?)", patients)

    # 2. Dummy Products
    # (name, category, price, cost, stock, min_stock, unit, expiry_date, description)
    products = [
        ('Paracetamol 500mg', 'Analgesik', 10000, 6000, 100, 20, 'Strip', '2027-12-01', 'Pereda nyeri dan demam'),
        ('Amoxicillin 500mg', 'Antibiotik', 25000, 15000, 5, 10, 'Strip', '2026-06-15', 'Obat infeksi bakteri'), # Low stock
        ('Cetirizine 10mg', 'Antihistamin', 15000, 8000, 50, 10, 'Strip', '2025-05-10', 'Obat alergi'), # Near expiry
        ('Amlodipine 5mg', 'Antihipertensi', 30000, 20000, 40, 10, 'Strip', '2027-01-20', 'Obat darah tinggi'),
        ('Metformin 500mg', 'Antidiabetik', 20000, 12000, 60, 10, 'Strip', '2026-11-11', 'Obat gula darah'),
        ('Vitamin C 1000mg', 'Suplemen', 50000, 30000, 150, 20, 'Botol', '2028-01-01', 'Meningkatkan imun tubuh'),
        ('Omeprazole 20mg', 'Gastrik', 40000, 25000, 8, 10, 'Strip', '2026-08-20', 'Obat asam lambung'), # Low stock
        ('Loperamide 2mg', 'Pencernaan', 12000, 7000, 30, 10, 'Strip', '2027-03-15', 'Obat diare'),
    ]
    cursor.executemany("INSERT INTO products (name, category, price, cost, stock, min_stock, unit, expiry_date, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", products)

    # 3. Dummy Suppliers
    suppliers = [
        ('Kimia Farma Dist', 'Bpk. Andi', '021-555123', 'Jakarta'),
        ('Indofarma Ltd', 'Ibu Maya', '021-444987', 'Bekasi'),
    ]
    cursor.executemany("INSERT INTO suppliers (name, contact_person, phone, address) VALUES (?, ?, ?, ?)", suppliers)

    # 4. Dummy Sales (Yesterday and Today)
    # Sale 1: Budi buys Paracetamol
    cursor.execute("INSERT INTO sales (patient_id, total_amount, payment_method, timestamp) VALUES (?, ?, ?, ?)", 
                   (1, 20000, 'Cash', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')))
    sale_id_1 = cursor.lastrowid
    cursor.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (?, ?, ?, ?)", (sale_id_1, 1, 2, 10000))

    # Sale 2: Siti buys Amlodipine and Vitamin C
    cursor.execute("INSERT INTO sales (patient_id, total_amount, payment_method, timestamp) VALUES (?, ?, ?, ?)", 
                   (2, 80000, 'Transfer', (datetime.now()).strftime('%Y-%m-%d %H:%M:%S')))
    sale_id_2 = cursor.lastrowid
    cursor.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (?, ?, ?, ?)", (sale_id_2, 4, 1, 30000))
    cursor.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (?, ?, ?, ?)", (sale_id_2, 6, 1, 50000))

    conn.commit()
    conn.close()
    print("Dummy data injected successfully!")

if __name__ == '__main__':
    init_dummy_data()
