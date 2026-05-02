from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "tokodewi_secret_key_999"

# Admin Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "dewi123"

BASE_DIR = '/root/.openclaw/workspace/App/tokodewi'
DATA_FILE = os.path.join(BASE_DIR, 'products.json')
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def load_json(file_path, default):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    products = load_json(DATA_FILE, [])
    settings = load_json(SETTINGS_FILE, {"shop_name": "Toko Dewi", "whatsapp": "628123456789", "description": "Menyediakan Pakaian & Bahan Makanan Berkualitas"})
    category = request.args.get('category')
    
    if category:
        filtered_products = [p for p in products if p['category'] == category]
    else:
        filtered_products = products
        
    return render_template('index.html', products=filtered_products, settings=settings, current_category=category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash('Kredensial salah!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    products = load_json(DATA_FILE, [])
    settings = load_json(SETTINGS_FILE, {})
    return render_template('admin.html', products=products, settings=settings)

@app.route('/admin/product/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    products = load_json(DATA_FILE, [])
    file = request.files.get('image')
    img_url = request.form.get('image_url')
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_url = f"/static/uploads/{filename}"
    
    new_id = max([p['id'] for p in products]) + 1 if products else 1
    products.append({
        "id": new_id,
        "name": request.form.get('name'),
        "category": request.form.get('category'),
        "price": request.form.get('price'),
        "desc": request.form.get('desc'),
        "image": img_url
    })
    save_json(DATA_FILE, products)
    return redirect(url_for('admin'))

@app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = load_json(DATA_FILE, [])
    product = next((p for p in products if p['id'] == id), None)
    
    if request.method == 'POST':
        file = request.files.get('image')
        img_url = request.form.get('image_url')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_url = f"/static/uploads/{filename}"
        elif not img_url:
            img_url = product['image']
            
        product.update({
            "name": request.form.get('name'),
            "category": request.form.get('category'),
            "price": request.form.get('price'),
            "desc": request.form.get('desc'),
            "image": img_url
        })
        save_json(DATA_FILE, products)
        return redirect(url_for('admin'))
        
    return render_template('edit_product.html', product=product)

@app.route('/admin/product/delete/<int:id>')
def delete_product(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = load_json(DATA_FILE, [])
    products = [p for p in products if p['id'] != id]
    save_json(DATA_FILE, products)
    return redirect(url_for('admin'))

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    settings = {
        "shop_name": request.form.get('shop_name'),
        "whatsapp": request.form.get('whatsapp'),
        "description": request.form.get('description')
    }
    save_json(SETTINGS_FILE, settings)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002)
