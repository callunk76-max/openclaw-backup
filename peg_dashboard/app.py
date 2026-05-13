#!/usr/bin/env python3
"""Dashboard Data Kepegawaian - Pemkab Bulukumba"""
import json, os, urllib.parse, re
from flask import Flask, render_template, request, jsonify
from upload_handler import process_uploaded_files

# Golongan index for sorting (higher = more senior)
GOL_INDEX = {"I/a":1,"I/b":2,"I/c":3,"I/d":4,"II/a":5,"II/b":6,"II/c":7,"II/d":8,
              "III/a":9,"III/b":10,"III/c":11,"III/d":12,"IV/a":13,"IV/b":14,"IV/c":15,"IV/d":16,"IV/e":17}

def hierarki_level(jabatan):
    """Tentukan level hierarki jabatan (1=tertinggi, 7=terendah)."""
    j = jabatan.upper() if jabatan else ""
    
    # Level 1: Pimpinan Tinggi (Eselon II)
    pimpinan = ['KEPALA DINAS','KEPALA BADAN','SEKRETARIS DAERAH','STAF AHLI']
    for p in pimpinan:
        if p in j and 'SUB' not in j:
            return 1
    # Asisten Setda (bukan JF Asisten Apoteker)
    if (' ASISTEN ' in j or j.startswith('ASISTEN ')) and 'JF ' not in j:
        return 1
    # Inspektur (bukan Inspektur Pembantu)
    if j == 'INSPEKTUR' or j.startswith('INSPEKTUR DAERAH') or j.startswith('PLT INSPEKTUR'):
        return 1
    
    # Level 2: Administrator (Eselon III)
    admin = ['KEPALA BIDANG','KEPALA BAGIAN','SEKRETARIS DINAS','SEKRETARIS BADAN',
             'SEKRETARIS DPRD','PLT KEPALA','KEPALA UPT','KEPALA UPTD','DIREKTUR',
             'KEPALA PELAKSANA']
    for a in admin:
        if a in j and 'SUB' not in j:
            return 2
    
    # Level 3: JF Ahli Madya
    if 'JF ' in j or j.startswith('JF'):
        if 'MADYA' in j or 'AHLI MADYA' in j:
            return 3
        if 'MUDA' in j or 'AHLI MUDA' in j:
            return 4
        if 'PERTAMA' in j or 'AHLI PERTAMA' in j:
            return 5
        if 'TERAMPIL' in j or 'PENYULUH' in j:
            return 6
        return 4  # default JF
    
    # Level 4: Pengawas (Eselon IV)
    pengawas = ['KEPALA SUB BIDANG','KEPALA SUB BAGIAN','KASUBAG','KASUBID',
                'SUB BAGIAN','SUB BIDANG','KEPALA SEKSI','KASI']
    for p in pengawas:
        if p in j:
            return 4
    
    # Level 5: JF non-spesifik / Tenaga Ahli
    if any(x in j for x in ['JF','ANALIS','PRANATA','ARSIPARIS','PUSTAKAWAN']):
        return 5
    
    # Level 6: Pelaksana / Staf
    pelaksana = ['PELAKSANA','BENDAHARA','STAF','PENGELOLA','PENGOLAH',
                 'PENYUSUN','ADMINISTRASI','OPERATOR','TEKNISI']
    for p in pelaksana:
        if p in j:
            return 6
    
    # Level 7: Juru / Lainnya
    if 'JURU' in j:
        return 7
    
    return 8

def sort_key_pegawai(e):
    """Sort key: hierarki jabatan → golongan (senior first) → nama"""
    level = hierarki_level(e.get('jabatan', ''))
    gol = GOL_INDEX.get(e.get('golongan_kode', ''), 0)
    nama = e.get('nama', '').lower()
    return (level, -gol, nama)

app = Flask(__name__, static_url_path='/peg/static')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

@app.template_filter('urlencode')
def urlencode_filter(s):
    return urllib.parse.quote(s, safe='')

DATA_FILE = os.path.join(os.path.dirname(__file__), "pegawai.json")

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

@app.route("/")
def index():
    data = load_data()
    total_pegawai = sum(a['total'] for a in data)
    
    # Golongan distribution using normalized data
    gol_map = {}
    for a in data:
        for e in a['pegawai']:
            k = e.get('golongan_kode', '') or 'Unknown'
            p = e.get('golongan_pangkat', '') or 'Unknown'
            label = f"{p} ({k})" if k else 'Unknown'
            if label not in gol_map:
                gol_map[label] = {'kode': k, 'pangkat': p, 'count': 0}
            gol_map[label]['count'] += 1
    
    # Sort gol by count (terbanyak dulu) untuk chart
    gol_chart = sorted(gol_map.items(), key=lambda x: -x[1]['count'])
    
    # Gender stats
    total_l = sum(1 for a in data for e in a['pegawai'] if e.get('jenis_kelamin') == 'L')
    total_p = sum(1 for a in data for e in a['pegawai'] if e.get('jenis_kelamin') == 'P')
    
    # Pensiun stats
    aman = sum(1 for a in data for e in a['pegawai'] if e.get('status_pensiun') == 'Aman')
    dekat = sum(1 for a in data for e in a['pegawai'] if e.get('status_pensiun') == 'Dekat Pensiun')
    segera = sum(1 for a in data for e in a['pegawai'] if e.get('status_pensiun') == 'Segera Pensiun')
    sudah = sum(1 for a in data for e in a['pegawai'] if e.get('status_pensiun') == 'Sudah Pensiun')
    
    # Sort SKPD list: by total pegawai desc
    skpd_sorted = sorted(data, key=lambda a: -a['total'])
    
    return render_template("dashboard.html",
        skpd_list=skpd_sorted,
        total_pegawai=total_pegawai,
        total_skpd=len(data),
        total_l=total_l,
        total_p=total_p,
        pensiun_aman=aman,
        pensiun_dekat=dekat,
        pensiun_segera=segera,
        pensiun_sudah=sudah,
        gol_distribution=gol_chart
    )

@app.route("/skpd/<path:name>")
def skpd_detail(name):
    data = load_data()
    agency = None
    for a in data:
        if a['skpd'] == name:
            agency = a
            break
    if not agency:
        return "SKPD tidak ditemukan", 404
    
    # Gol distribution (active vs pensiun)
    gol_count = {}
    for e in agency['pegawai']:
        k = e.get('golongan_kode', '') or 'Unknown'
        p = e.get('golongan_pangkat', '') or 'Unknown'
        label = f"{p} ({k})" if k else 'Unknown'
        if label not in gol_count:
            gol_count[label] = {'total': 0, 'pensiun': 0}
        gol_count[label]['total'] += 1
        if e.get('status_pensiun') == 'Sudah Pensiun':
            gol_count[label]['pensiun'] += 1
    
    # Gender stats for this SKPD
    skpd_l = sum(1 for e in agency['pegawai'] if e.get('jenis_kelamin') == 'L')
    skpd_p = sum(1 for e in agency['pegawai'] if e.get('jenis_kelamin') == 'P')
    
    # Pensiun stats per SKPD
    skpd_aman = sum(1 for e in agency['pegawai'] if e.get('status_pensiun') == 'Aman')
    skpd_dekat = sum(1 for e in agency['pegawai'] if e.get('status_pensiun') == 'Dekat Pensiun')
    skpd_segera = sum(1 for e in agency['pegawai'] if e.get('status_pensiun') == 'Segera Pensiun')
    skpd_sudah = sum(1 for e in agency['pegawai'] if e.get('status_pensiun') == 'Sudah Pensiun')
    
    # Sort: hierarki jabatan (tertinggi dulu) → golongan (senior dulu) → nama
    sorted_pegawai = sorted(agency['pegawai'], key=sort_key_pegawai)

    # Sort untuk chart (by count terbanyak)
    gol_chart = sorted(gol_count.items(), key=lambda x: -x[1]['total'])
    
    # Sort untuk tabel rincian (by hierarki golongan tertinggi)
    def gol_sort_key(item):
        label, info = item
        kode = label.split('(')[-1].rstrip(')').strip() if '(' in label else ''
        idx = GOL_INDEX.get(kode, 0)
        return (-idx, -info['total'])
    gol_table = sorted(gol_count.items(), key=gol_sort_key)

    return render_template("skpd.html",
        skpd=agency['skpd'],
        total=agency['total'],
        pegawai=sorted_pegawai,
        skpd_l=skpd_l,
        skpd_p=skpd_p,
        skpd_aman=skpd_aman,
        skpd_dekat=skpd_dekat,
        skpd_segera=skpd_segera,
        skpd_sudah=skpd_sudah,
        gol_chart=gol_chart,
        gol_table=gol_table
    )

@app.route("/api/search")
def api_search():
    q = request.args.get('q', '').lower()
    if len(q) < 2:
        return jsonify({"results": []})
    
    data = load_data()
    results = []
    for a in data:
        for e in a['pegawai']:
            if q in e['nama'].lower() or q in e['nip']:
                results.append({
                    "nama": e['nama'],
                    "nip": e['nip'],
                    "golongan": e['golongan'],
                    "jabatan": e['jabatan'][:60],
                    "skpd": a['skpd']
                })
                if len(results) >= 50:
                    break
        if len(results) >= 50:
            break
    
    return jsonify({"results": results})

@app.route("/upload", methods=["POST"])
def upload():
    if 'files[]' not in request.files:
        return jsonify({"ok": False, "message": "Tidak ada file"})
    files = request.files.getlist('files[]')
    result = process_uploaded_files(files)
    return jsonify(result)

@app.route("/api/skpd/<path:name>")
def api_skpd(name):
    data = load_data()
    for a in data:
        if a['skpd'] == name:
            return jsonify(a)
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)
