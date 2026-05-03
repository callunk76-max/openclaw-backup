from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import os
import time

app = Flask(__name__)
app.secret_key = "filebox_bulukumba_2026"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
PASSWORD = "13Kholil"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_files():
    files = []
    try:
        for f in os.listdir(UPLOAD_FOLDER):
            fp = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(fp):
                size = os.path.getsize(fp)
                mtime = os.path.getmtime(fp)
                files.append({
                    'name': f,
                    'size': size,
                    'size_str': format_size(size),
                    'mtime': time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime))
                })
    except Exception:
        pass
    files.sort(key=lambda x: x['mtime'], reverse=True)
    return files

def format_size(size):
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024*1024*1024):.1f} GB"
    elif size >= 1024 * 1024:
        return f"{size / (1024*1024):.1f} MB"
    elif size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"

@app.route('/')
def index():
    if not session.get('filebox_logged_in'):
        return redirect(url_for('login'))
    files = get_files()
    return render_template('index.html', files=files)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['filebox_logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Password salah!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('filebox_logged_in', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('filebox_logged_in'):
        return redirect(url_for('login'))
    file = request.files.get('file')
    if file and file.filename:
        # Sanitize filename (remove path separators)
        filename = file.filename.replace('/', '_').replace('\\', '_')
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
    return redirect(url_for('index'))

@app.route('/download/<path:filename>')
def download(filename):
    if not session.get('filebox_logged_in'):
        return redirect(url_for('login'))
    # Security: prevent directory traversal
    safe_name = os.path.basename(filename)
    return send_from_directory(UPLOAD_FOLDER, safe_name, as_attachment=False)

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    if not session.get('filebox_logged_in'):
        return redirect(url_for('login'))
    safe_name = os.path.basename(filename)
    filepath = os.path.join(UPLOAD_FOLDER, safe_name)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5007, debug=True)
