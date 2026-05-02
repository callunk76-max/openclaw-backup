from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mokidonut_secret_key_123"

# Admin Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "mokidonate123"

DATA_FILE = '/root/.openclaw/workspace/App/mokidonut/donuts.json'
SETTINGS_FILE = '/root/.openclaw/workspace/App/mokidonut/settings.json'
UPLOAD_FOLDER = '/root/.openclaw/workspace/App/mokidonut/static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def load_donuts():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_donuts(donuts):
    with open(DATA_FILE, 'w') as f:
        json.dump(donuts, f, indent=4)

def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"shop_name": "MokiDonut", "shop_logo": "🍩", "whatsapp": "6285896743403"}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

@app.route('/')
def home():
    donuts = load_donuts()
    settings = load_settings()
    return render_template('index.html', donuts=donuts, settings=settings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return render_template('login.html', error="Kredensial salah!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    donuts = load_donuts()
    settings = load_settings()
    return render_template('admin.html', donuts=donuts, settings=settings)

@app.route('/admin/update_shop', methods=['POST'])
def update_shop():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    settings = load_settings()
    settings['shop_name'] = request.form.get('shop_name')
    settings['shop_logo'] = request.form.get('shop_logo')
    settings['whatsapp'] = request.form.get('whatsapp')
    
    save_settings(settings)
    return redirect(url_for('admin'))

@app.route('/admin/add', methods=['POST'])
def add_donut():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    donuts = load_donuts()
    
    file = request.files.get('img_file')
    img_url_from_form = request.form.get('img')
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        img_url = f"/static/uploads/{filename}"
    else:
        img_url = img_url_from_form
    
    new_id = max([d['id'] for d in donuts]) + 1 if donuts else 1
    new_donut = {
        "id": new_id,
        "name": request.form.get('name'),
        "price": request.form.get('price'),
        "img": img_url,
        "desc": request.form.get('desc')
    }
    donuts.append(new_donut)
    save_donuts(donuts)
    return redirect(url_for('admin'))

@app.route('/admin/update', methods=['POST'])
def update():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    donuts = load_donuts()
    donut_id = int(request.form.get('id'))
    
    file = request.files.get('img_file')
    img_url_from_form = request.form.get('img')
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        img_url = f"/static/uploads/{filename}"
    else:
        img_url = img_url_from_form
    
    for donut in donuts:
        if donut['id'] == donut_id:
            donut['name'] = request.form.get('name')
            donut['price'] = request.form.get('price')
            donut['img'] = img_url
            donut['desc'] = request.form.get('desc')
            break
    
    save_donuts(donuts)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
