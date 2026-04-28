import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "aramedica_pro_secret_2026"

DB_PATH = '/root/.openclaw/workspace/App/aramedica/pharmacy.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Products Table
        conn.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            cost REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            min_stock INTEGER DEFAULT 10,
            unit TEXT,
            expiry_date DATE,
            description TEXT
        )''')
        
        # Patients Table
        conn.execute('''CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            medical_history TEXT
        )''')

        # Sales Table
        conn.execute('''CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_id INTEGER,
            total_amount REAL,
            payment_method TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )''')

        # Sale Items Table
        conn.execute('''CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price_at_sale REAL,
            FOREIGN KEY(sale_id) REFERENCES sales(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )''')

        # Suppliers Table
        conn.execute('''CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            address TEXT
        )''')

        # Purchases Table (Stock In)
        conn.execute('''CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_cost REAL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )''')

        # Purchase Items Table
        conn.execute('''CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            cost_price REAL,
            FOREIGN KEY(purchase_id) REFERENCES purchases(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )''')
        conn.commit()

# Initialize DB on startup
init_db()

# --- AUTH ---
ADMIN_USER = "admin"
ADMIN_PASS = "aramedica123"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        flash('Kredensial salah!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- PUBLIC FRONTEND ---
@app.route('/')
def index():
    # Public view: just a professional landing page
    return render_template('index.html')

# --- ADMIN DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    with get_db() as conn:
        # Today's Revenue
        today = datetime.now().strftime('%Y-%m-%d')
        revenue = conn.execute("SELECT SUM(total_amount) FROM sales WHERE date(timestamp) = ?", (today,)).fetchone()[0] or 0
        
        # Low Stock Count
        low_stock = conn.execute("SELECT COUNT(*) FROM products WHERE stock <= min_stock").fetchone()[0]
        
        # Near Expiry (next 30 days)
        expiry_limit = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        near_expiry = conn.execute("SELECT COUNT(*) FROM products WHERE expiry_date <= ? AND expiry_date >= date('now')", (expiry_limit,)).fetchone()[0]
        
        # Total Patients
        total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]

    return render_template('admin/dashboard.html', revenue=revenue, low_stock=low_stock, near_expiry=near_expiry, patients=total_patients)

# --- POS / TRANSACTIONS ---
@app.route('/pos')
def pos():
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products WHERE stock > 0").fetchall()
        patients = conn.execute("SELECT id, name FROM patients").fetchall()
    return render_template('admin/pos.html', products=products, patients=patients)

@app.route('/api/sale', methods=['POST'])
def process_sale():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    items = data.get('items', [])
    patient_id = data.get('patient_id')
    payment_method = data.get('payment_method', 'Cash')
    total = data.get('total', 0)

    if not items: return jsonify({"error": "No items"}), 400

    try:
        with get_db() as conn:
            # Create Sale
            cur = conn.execute("INSERT INTO sales (patient_id, total_amount, payment_method) VALUES (?, ?, ?)", 
                               (patient_id, total, payment_method))
            sale_id = cur.lastrowid
            
            for item in items:
                # Update Stock
                conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
                # Add Item
                conn.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (?, ?, ?, ?)", 
                             (sale_id, item['id'], item['qty'], item['price']))
            conn.commit()
        return jsonify({"success": True, "sale_id": sale_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- INVENTORY / WAREHOUSE ---
@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    return render_template('admin/inventory.html', products=products)

@app.route('/inventory/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db() as conn:
        conn.execute('''INSERT INTO products (name, category, price, cost, stock, min_stock, unit, expiry_date, description) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                     (request.form.get('name'), request.form.get('category'), request.form.get('price'), 
                      request.form.get('cost'), request.form.get('stock'), request.form.get('min_stock'), 
                      request.form.get('unit'), request.form.get('expiry_date'), request.form.get('description')))
        conn.commit()
    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<int:id>', methods=['POST'])
def edit_product(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db() as conn:
        conn.execute('''UPDATE products SET name=?, category=?, price=?, cost=?, stock=?, min_stock=?, unit=?, expiry_date=?, description=? 
                        WHERE id=?''', 
                     (request.form.get('name'), request.form.get('category'), request.form.get('price'), 
                      request.form.get('cost'), request.form.get('stock'), request.form.get('min_stock'), 
                      request.form.get('unit'), request.form.get('expiry_date'), request.form.get('description'), id))
        conn.commit()
    return redirect(url_for('inventory'))

# --- ACCOUNTING / FINANCE ---
@app.route('/finance')
def finance():
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db() as conn:
        # Total Revenue
        revenue = conn.execute("SELECT SUM(total_amount) FROM sales").fetchone()[0] or 0
        
        # Total COGS (Cost of Goods Sold)
        cogs = conn.execute('''
            SELECT SUM(si.quantity * p.cost) 
            FROM sale_items si 
            JOIN products p ON si.product_id = p.id
        ''').fetchone()[0] or 0
        
        profit = revenue - cogs
        
        # Recent Sales
        recent_sales = conn.execute("SELECT * FROM sales ORDER BY timestamp DESC LIMIT 10").fetchall()

    return render_template('admin/finance.html', revenue=revenue, cogs=cogs, profit=profit, sales=recent_sales)

# --- PATIENT RECORDS ---
@app.route('/patients')
def patients():
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db() as conn:
        patients = conn.execute("SELECT * FROM patients ORDER BY name").fetchall()
    return render_template('admin/patients.html', patients=patients)

@app.route('/patients/add', methods=['POST'])
def add_patient():
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db() as conn:
        conn.execute("INSERT INTO patients (name, phone, address, medical_history) VALUES (?, ?, ?, ?)", 
                     (request.form.get('name'), request.form.get('phone'), request.form.get('address'), request.form.get('medical_history')))
        conn.commit()
    return redirect(url_for('patients'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
