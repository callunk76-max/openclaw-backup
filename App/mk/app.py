"""Farmasi Puskesmas Ujung Loe — Flask App"""
import os, sys, json, re
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS

# Monkey-patch sub_filter support for Flask redirects
BASE = '/mk'  # nginx sub-path

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'instance', 'farmasi.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, Desa, KategoriItem, ItemFarmasi, UnitPelayanan, Dokter, Pasien
from models import Resep, ResepItem, Racikan, RacikanKomponen
from models import Stok, MutasiStok, Distribusi, DistribusiItem, LaporanPustu, LaporanPustuItem
db.init_app(app)

with app.app_context():
    db.create_all()
    from seed_data import seed_all
    seed_all()

CORS(app)

# ─── Context processor ─────────────────────────────
@app.context_processor
def inject_globals():
    return dict(
        now=datetime.now(), BASE=BASE,
        today=date.today().isoformat()
    )

# ─── Helper ─────────────────────────────────────────
def make_no_resep():
    today = date.today().strftime('%Y%m%d')
    last = Resep.query.filter(Resep.no_resep.like(f'R-{today}-%')).order_by(Resep.id.desc()).first()
    n = 1 if not last else int(last.no_resep.split('-')[-1]) + 1
    return f'R-{today}-{n:03d}'

def json_ok(data=None, msg='ok'):
    return jsonify(success=True, message=msg, data=data)

def json_err(msg='error', code=400):
    return jsonify(success=False, message=msg), code

# ─── Dashboard ──────────────────────────────────────
@app.route('/')
def dashboard():
    stats = {
        'resep_hari_ini': Resep.query.filter(Resep.tanggal == date.today()).count(),
        'pasien_total': Pasien.query.count(),
        'obat_total': ItemFarmasi.query.filter_by(tipe='obat').count(),
        'bhp_total': ItemFarmasi.query.filter_by(tipe='bhp').count(),
        'stok_kritis': Stok.query.filter(Stok.qty < 5).count(),
        'resep_menunggu': Resep.query.filter_by(tanggal=date.today(), status='baru').count()
    }
    return render_template('dashboard.html', stats=stats)

# ─── CRUD: Pasien ──────────────────────────────────
@app.route('/pasien')
def pasien_list():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    query = Pasien.query
    if q:
        query = query.filter(Pasien.nama.contains(q) | Pasien.nik.contains(q) | Pasien.no_bpjs.contains(q))
    pagination = query.order_by(Pasien.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('pasien/list.html', pasien=pagination.items, pagination=pagination, q=q)

@app.route('/pasien/tambah', methods=['GET', 'POST'])
def pasien_tambah():
    if request.method == 'POST':
        d = request.form
        pasien = Pasien(
            nik=d.get('nik'), no_bpjs=d.get('no_bpjs'), nama=d.get('nama'),
            jenis_kelamin=d.get('jenis_kelamin'), tempat_lahir=d.get('tempat_lahir'),
            tanggal_lahir=date.fromisoformat(d['tanggal_lahir']), alamat=d.get('alamat'),
            desa_id=int(d['desa_id']) if d.get('desa_id') else None,
            telepon=d.get('telepon'), pekerjaan=d.get('pekerjaan')
        )
        db.session.add(pasien)
        db.session.commit()
        return redirect(f'{BASE}/pasien')
    desa = Desa.query.all()
    return render_template('pasien/form.html', desa=desa, pasien=None)

@app.route('/pasien/<int:id>/edit', methods=['GET', 'POST'])
def pasien_edit(id):
    pasien = Pasien.query.get_or_404(id)
    if request.method == 'POST':
        d = request.form
        pasien.nik = d.get('nik'); pasien.no_bpjs = d.get('no_bpjs')
        pasien.nama = d.get('nama'); pasien.jenis_kelamin = d.get('jenis_kelamin')
        pasien.tempat_lahir = d.get('tempat_lahir')
        pasien.tanggal_lahir = date.fromisoformat(d['tanggal_lahir'])
        pasien.alamat = d.get('alamat')
        pasien.desa_id = int(d['desa_id']) if d.get('desa_id') else None
        pasien.telepon = d.get('telepon'); pasien.pekerjaan = d.get('pekerjaan')
        db.session.commit()
        return redirect(f'{BASE}/pasien')
    desa = Desa.query.all()
    return render_template('pasien/form.html', desa=desa, pasien=pasien)

@app.route('/api/pasien/search')
def api_pasien_search():
    q = request.args.get('q', '')
    if len(q) < 2: return json_ok([])
    pasien = Pasien.query.filter(
        Pasien.nama.contains(q) | Pasien.nik.contains(q) | Pasien.no_bpjs.contains(q)
    ).limit(10).all()
    return json_ok([{
        'id': p.id, 'nama': p.nama, 'nik': p.nik,
        'no_bpjs': p.no_bpjs, 'desa': p.desa.nama if p.desa else ''
    } for p in pasien])

# ─── Resep ──────────────────────────────────────────
@app.route('/resep')
def resep_list():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    query = Resep.query
    if q:
        query = query.join(Pasien).filter(
            Pasien.nama.contains(q) | Resep.no_resep.contains(q))
    pagination = query.order_by(Resep.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('resep/list.html', resep=pagination.items, pagination=pagination, q=q)

@app.route('/resep/baru', methods=['GET', 'POST'])
def resep_baru():
    if request.method == 'POST':
        d = request.form
        resep = Resep(
            no_resep=make_no_resep(), tanggal=date.today(),
            jenis_pelayanan=d['jenis_pelayanan'], no_rm=d.get('no_rm'),
            no_kamar=d.get('no_kamar'), pasien_id=int(d['pasien_id']),
            dokter_id=int(d['dokter_id']), unit_id=1,
            keluhan=d.get('keluhan'), jaminan=d['jaminan'],
            no_sep=d.get('no_sep'), created_by='Admin'
        )
        db.session.add(resep)
        db.session.flush()

        # Parse items
        obat_ids = request.form.getlist('obat_id[]')
        qtys = request.form.getlist('qty[]')
        aturans = request.form.getlist('aturan[]')
        for i, oid in enumerate(obat_ids):
            if not oid: continue
            ri = ResepItem(
                resep_id=resep.id, item_id=int(oid),
                qty=float(qtys[i]) if i < len(qtys) else 1,
                aturan=aturans[i] if i < len(aturans) else ''
            )
            db.session.add(ri)
            # Kurangi stok
            stok = Stok.query.filter_by(unit_id=1, item_id=int(oid)).first()
            if stok and stok.qty >= float(qtys[i]):
                stok.qty -= float(qtys[i])

        db.session.commit()
        return redirect(f'{BASE}/resep/{resep.id}')

    pasien = Pasien.query.order_by(Pasien.nama).limit(20).all()
    dokter = Dokter.query.filter_by(aktif=True).all()
    items = ItemFarmasi.query.filter_by(aktif=True).order_by(ItemFarmasi.nama_generik).all()
    items_json = [{'id': i.id, 'nama': str(i), 'satuan': i.satuan, 'kategori': i.kategori.nama if i.kategori else ''} for i in items]
    return render_template('resep/form.html', pasien=pasien, dokter=dokter, items=items, items_json=items_json)

@app.route('/resep/<int:id>')
def resep_detail(id):
    resep = Resep.query.get_or_404(id)
    return render_template('resep/detail.html', resep=resep)

@app.route('/api/resep/<int:id>/status', methods=['POST'])
def resep_status(id):
    resep = Resep.query.get_or_404(id)
    status = request.json.get('status')
    resep.status = status
    db.session.commit()
    return json_ok(msg=f'Status → {status}')

# ─── Obat & BHP ────────────────────────────────────
@app.route('/obat')
def obat_list():
    tipe = request.args.get('tipe', 'obat')
    q = request.args.get('q', '')
    kat_id = request.args.get('kategori', type=int)
    page = request.args.get('page', 1, type=int)

    query = ItemFarmasi.query.filter_by(tipe=tipe)
    if q: query = query.filter(ItemFarmasi.nama_generik.contains(q))
    if kat_id: query = query.filter_by(kategori_id=kat_id)
    pagination = query.order_by(ItemFarmasi.nama_generik).paginate(page=page, per_page=20, error_out=False)

    kategori = KategoriItem.query.filter_by(tipe=tipe).all()
    return render_template('master/obat.html', items=pagination.items, pagination=pagination,
                          kategori=kategori, q=q, tipe=tipe, kat_id=kat_id)

@app.route('/api/obat/search')
def api_obat_search():
    q = request.args.get('q', '')
    tipe = request.args.get('tipe', 'obat')
    if len(q) < 1: return json_ok([])
    items = ItemFarmasi.query.filter(
        ItemFarmasi.nama_generik.contains(q),
        ItemFarmasi.tipe == tipe,
        ItemFarmasi.aktif == True
    ).limit(15).all()
    return json_ok([{
        'id': i.id, 'nama': str(i),
        'bentuk': i.bentuk, 'kekuatan': i.kekuatan,
        'satuan': i.satuan, 'tipe': i.tipe,
        'kategori': i.kategori.nama if i.kategori else ''
    } for i in items])

# ─── Stok ──────────────────────────────────────────
@app.route('/stok')
def stok_list():
    unit_id = request.args.get('unit_id', 1, type=int)
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    query = Stok.query.filter_by(unit_id=unit_id).join(ItemFarmasi)
    if q: query = query.filter(ItemFarmasi.nama_generik.contains(q))
    pagination = query.order_by(Stok.qty.asc()).paginate(page=page, per_page=20, error_out=False)

    units = UnitPelayanan.query.all()
    return render_template('stok/list.html', stok=pagination.items, pagination=pagination,
                          units=units, unit_id=unit_id, q=q)

@app.route('/stok/masuk', methods=['GET', 'POST'])
def stok_masuk():
    if request.method == 'POST':
        d = request.form
        item_id = int(d['item_id'])
        qty = float(d['qty'])
        ed = date.fromisoformat(d['ed']) if d.get('ed') else None

        stok = Stok.query.filter_by(unit_id=1, item_id=item_id, batch=d.get('batch')).first()
        if stok:
            stok.qty += qty
        else:
            stok = Stok(unit_id=1, item_id=item_id, qty=qty,
                       batch=d.get('batch'), ed=ed, harga_beli=float(d['harga_beli']) if d.get('harga_beli') else 0)
            db.session.add(stok)
        db.session.flush()

        db.session.add(MutasiStok(
            stok_id=stok.id, tipe='masuk', qty=qty, sisa_stok=stok.qty,
            keterangan=d.get('keterangan'), user='Admin'))
        db.session.commit()
        return redirect(f'{BASE}/stok')

    items = ItemFarmasi.query.filter_by(aktif=True).order_by(ItemFarmasi.nama_generik).all()
    return render_template('stok/masuk.html', items=items)

@app.route('/stok/opname', methods=['GET', 'POST'])
def stok_opname():
    if request.method == 'POST':
        for key, val in request.form.items():
            if key.startswith('qty_'):
                stok_id = int(key.split('_')[1])
                new_qty = float(val)
                stok = Stok.query.get(stok_id)
                if stok and stok.qty != new_qty:
                    diff = new_qty - stok.qty
                    db.session.add(MutasiStok(
                        stok_id=stok.id, tipe='opname', qty=diff,
                        sisa_stok=new_qty, user='Admin'))
                    stok.qty = new_qty
        db.session.commit()
        return redirect(f'{BASE}/stok')

    stok_list = Stok.query.filter_by(unit_id=1).join(ItemFarmasi).order_by(ItemFarmasi.nama_generik).all()
    return render_template('stok/opname.html', stok_list=stok_list)

# ─── Distribusi ─────────────────────────────────────
@app.route('/distribusi')
def distribusi_list():
    page = request.args.get('page', 1, type=int)
    pagination = Distribusi.query.order_by(Distribusi.id.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('stok/distribusi_list.html', distribusi=pagination.items, pagination=pagination)

@app.route('/distribusi/baru', methods=['GET', 'POST'])
def distribusi_baru():
    if request.method == 'POST':
        d = request.form
        no = f'DIS-{date.today().strftime("%Y%m%d")}-{Distribusi.query.count()+1:03d}'
        dis = Distribusi(
            dari_unit_id=1, ke_unit_id=int(d['ke_unit_id']),
            tanggal=date.today(), no_distribusi=no,
            keterangan=d.get('keterangan'), created_by='Admin'
        )
        db.session.add(dis)
        db.session.flush()

        item_ids = request.form.getlist('item_id[]')
        qtys = request.form.getlist('qty[]')
        for i, iid in enumerate(item_ids):
            if not iid: continue
            q = float(qtys[i])
            db.session.add(DistribusiItem(distribusi_id=dis.id, item_id=int(iid), qty=q))
            # Kurangi stok puskesmas
            stok = Stok.query.filter_by(unit_id=1, item_id=int(iid)).first()
            if stok and stok.qty >= q:
                stok.qty -= q
        db.session.commit()
        return redirect(f'{BASE}/distribusi')

    units = UnitPelayanan.query.filter(UnitPelayanan.tipe != 'puskesmas').all()
    items = ItemFarmasi.query.filter_by(aktif=True).order_by(ItemFarmasi.nama_generik).all()
    return render_template('stok/distribusi_form.html', units=units, items=items)

# ─── Laporan ────────────────────────────────────────
@app.route('/laporan')
def laporan_index():
    return render_template('laporan/index.html')

@app.route('/laporan/lplpo')
def laporan_lplpo():
    bulan = request.args.get('bulan', type=int, default=date.today().month)
    tahun = request.args.get('tahun', type=int, default=date.today().year)
    unit_id = request.args.get('unit_id', 1, type=int)

    items = ItemFarmasi.query.filter_by(tipe='obat', aktif=True).order_by(ItemFarmasi.nama_generik).all()
    laporan_data = []
    for item in items:
        stok = Stok.query.filter_by(unit_id=unit_id, item_id=item.id).first()
        laporan_data.append({
            'item': item,
            'stok': stok.qty if stok else 0,
        })
    units = UnitPelayanan.query.all()
    return render_template('laporan/lplpo.html', items=laporan_data, bulan=bulan, tahun=tahun, units=units, unit_id=unit_id)

@app.route('/laporan/resep-harian')
def laporan_resep_harian():
    tgl = request.args.get('tgl', date.today().isoformat())
    tgl_date = date.fromisoformat(tgl)
    resep = Resep.query.filter(Resep.tanggal == tgl_date).order_by(Resep.id).all()
    return render_template('laporan/resep_harian.html', resep=resep, tgl=tgl)

# ─── API Stats ──────────────────────────────────────
@app.route('/api/stats')
def api_stats():
    now = date.today()
    return json_ok({
        'resep_hari_ini': Resep.query.filter(Resep.tanggal == now).count(),
        'resep_bulan_ini': Resep.query.filter(
            db.extract('month', Resep.tanggal) == now.month,
            db.extract('year', Resep.tanggal) == now.year
        ).count(),
        'stok_kritis': Stok.query.filter(Stok.qty < 5).count(),
        'obat': ItemFarmasi.query.filter_by(tipe='obat').count(),
        'bhp': ItemFarmasi.query.filter_by(tipe='bhp').count(),
    })

@app.route('/reset-data', methods=['POST'])
def reset_data():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()
    from seed_data import seed_all
    seed_all()
    return jsonify(success=True, message='Data direset')

# ─── Start ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
