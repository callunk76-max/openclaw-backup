import os, json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "ar_verif_dashboard_2026"
app.config['MAX_CONTENT_LENGTH'] = 110 * 1024 * 1024  # 110MB

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DATA_FILE = os.path.join(DATA_DIR, 'Data_Verif.xlsx')
DEFAULT_SOURCE = '/root/.openclaw/workspace/App/filebox/uploads/Data Verif.xlsx'

BULAN_IND = {
    'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4,
    'Mei': 5, 'Juni': 6, 'Juli': 7, 'Agustus': 8,
    'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
}
BLN_KE_IND = {v: k for k, v in BULAN_IND.items()}

def copy_default_data():
    if not os.path.exists(DATA_FILE) and os.path.exists(DEFAULT_SOURCE):
        import shutil
        shutil.copy2(DEFAULT_SOURCE, DATA_FILE)
        app.logger.info(f"Copied default data from {DEFAULT_SOURCE}")

copy_default_data()

def normalisasi_tanggal(tgl):
    """Convert any date format to 'DD Bulan YYYY' Indonesian format."""
    if pd.isna(tgl):
        return '-'
    tgl_str = str(tgl).strip()

    # Already in Indonesian format "DD Bulan YYYY" — ensure zero-padded day
    for bulan in BULAN_IND:
        pattern = rf'(\d{{1,2}})\s+({bulan})\s+(\d{{4}})'
        match = re.search(pattern, tgl_str)
        if match:
            d, bln, y = int(match.group(1)), match.group(2), int(match.group(3))
            return f'{d:02d} {bln} {y}'

    # ISO format "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD"
    iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', tgl_str)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        bln = BLN_KE_IND.get(m, 'Unknown')
        return f'{d:02d} {bln} {y}'

    # Excel serial number (datetime object)
    if hasattr(tgl, 'strftime'):
        return tgl.strftime('%d %B %Y')  # %d already zero-padded

    return tgl_str

def load_data():
    """Load xlsx into DataFrame, return df or None."""
    if not os.path.exists(DATA_FILE):
        return None
    try:
        df = pd.read_excel(DATA_FILE)
        df.columns = df.columns.str.strip()
        # Standardize all dates
        df['Tgl. Pengajuan'] = df['Tgl. Pengajuan'].apply(normalisasi_tanggal)
        return df
    except Exception as e:
        app.logger.error(f"Error reading xlsx: {e}")
        return None

@app.route('/')
def index():
    df = load_data()
    if df is None:
        return render_template('index.html', data=None, stats=None)

    # Deduplicate: if same Nama Pemohon + Satuan Kerja + Role, keep latest (highest No.)
    # (beda role dianggap entri berbeda)
    df_dedup = df.sort_values('No.', ascending=True).drop_duplicates(
        subset=['Nama Pemohon', 'Satuan Kerja', 'Role'], keep='last')
    total = len(df_dedup)
    status_counts = df_dedup['Status'].value_counts().to_dict()
    role_counts = df_dedup['Role'].value_counts().to_dict()

    # Role breakdown table
    role_table = df_dedup.groupby('Role').agg(
        Jumlah=('Status', 'count'),
        Diterima=('Status', lambda x: (x == 'Diterima').sum()),
        Ditolak=('Status', lambda x: (x == 'Ditolak').sum()),
        Tidak_Aktif=('Status', lambda x: (x == 'Tidak Aktif').sum()),
    ).reset_index()
    role_table['%'] = (role_table['Diterima'] / role_table['Jumlah'] * 100).round(1)
    role_table = role_table.sort_values('Jumlah', ascending=False)
    role_list = role_table.to_dict('records')

    # OPD/Satker breakdown
    skpd_table = df_dedup.groupby('Satuan Kerja').agg(
        Jumlah=('Status', 'count'),
        Diterima=('Status', lambda x: (x == 'Diterima').sum()),
        Ditolak=('Status', lambda x: (x == 'Ditolak').sum()),
    ).reset_index()
    skpd_table['%'] = (skpd_table['Diterima'] / skpd_table['Jumlah'] * 100).round(1)
    skpd_table = skpd_table.sort_values('Jumlah', ascending=False)
    skpd_top = skpd_table.to_dict('records')
    skpd_all = skpd_table.to_dict('records')

    # Latest pemohon from dedup
    df_newest = df_dedup.sort_values('No.', ascending=False).head(10).to_dict('records')

    # All data for client-side
    all_data = df_dedup.sort_values('No.', ascending=True).to_dict('records')

    stats = {
        'total': total,
        'diterima': status_counts.get('Diterima', 0),
        'ditolak': status_counts.get('Ditolak', 0),
        'tidak_aktif': status_counts.get('Tidak Aktif', 0),
        'verifikasi': status_counts.get('Sedang Verifikasi', 0),
        'diterima_pct': round(status_counts.get('Diterima', 0) / total * 100, 1) if total else 0,
        'ditolak_pct': round(status_counts.get('Ditolak', 0) / total * 100, 1) if total else 0,
        'tidak_aktif_pct': round(status_counts.get('Tidak Aktif', 0) / total * 100, 1) if total else 0,
        'verifikasi_pct': round(status_counts.get('Sedang Verifikasi', 0) / total * 100, 1) if total else 0,
        'roles': role_counts,
    }

    return render_template('index.html',
        data=all_data, stats=stats,
        role_list=role_list, skpd_top=skpd_top,
        skpd_all=skpd_all, skpd_counts=skpd_table.set_index('Satuan Kerja')['Jumlah'].to_dict(),
        pemohon_terbaru=df_newest)


@app.route('/api/data')
def api_data():
    df = load_data()
    if df is None:
        return jsonify({'error': 'No data'}), 404

    status_filter = request.args.get('status')
    role_filter = request.args.get('role')
    search = request.args.get('search', '').strip().lower()

    if status_filter:
        df = df[df['Status'] == status_filter]
    if role_filter:
        df = df[df['Role'] == role_filter]
    if search:
        mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(search, na=False).any(), axis=1)
        df = df[mask]

    sort_col = request.args.get('sort', 'No.')
    sort_dir = request.args.get('dir', 'desc')
    if sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=(sort_dir == 'asc'))

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    total = len(df)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = df.iloc[start:end].to_dict('records')

    return jsonify({
        'data': page_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    })


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Tidak ada file yang dipilih!')
            return redirect(url_for('upload'))
        file = request.files['file']
        if file.filename == '':
            flash('Nama file kosong!')
            return redirect(url_for('upload'))
        if not file.filename.lower().endswith('.xlsx'):
            flash('Hanya file .xlsx yang diperbolehkan!')
            return redirect(url_for('upload'))

        try:
            df = pd.read_excel(file)
            file.seek(0)
            file.save(DATA_FILE)
            flash(f'✅ Data berhasil diupload! {len(df)} entri dimuat.')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'❌ Gagal membaca file: {str(e)}')
            return redirect(url_for('upload'))

    info = None
    if os.path.exists(DATA_FILE):
        df = load_data()
        if df is not None:
            mtime = os.path.getmtime(DATA_FILE)
            info = {
                'rows': len(df),
                'cols': len(df.columns),
                'columns': list(df.columns),
                'last_updated': datetime.fromtimestamp(mtime).strftime('%d %B %Y %H:%M'),
                'filename': os.path.basename(DATA_FILE),
            }

    return render_template('upload.html', info=info)


@app.route('/reset-data')
def reset_data():
    import shutil
    if os.path.exists(DEFAULT_SOURCE):
        shutil.copy2(DEFAULT_SOURCE, DATA_FILE)
        flash('✅ Data berhasil di-reset ke default!')
    else:
        flash('⚠️ File default tidak ditemukan.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5003, debug=True)
