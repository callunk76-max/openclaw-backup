from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date
from models import db, Stok, Obat, Adjustment, Pembelian, User

stok_bp = Blueprint('stok', __name__, url_prefix='/stok')


@stok_bp.before_request
def check_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))


# ─── KARTU STOK ────────────────────────────────────────

@stok_bp.route('/')
def stok_index():
    search = request.args.get('search', '')
    q = Obat.query.filter_by(is_active=True)
    if search:
        q = q.filter(db.or_(Obat.nama_generik.ilike(f'%{search}%'),
                            Obat.kode_obat.ilike(f'%{search}%')))
    obat_list = q.order_by(Obat.nama_generik).all()
    return render_template('stok_index.html', obat_list=obat_list, search=search)


@stok_bp.route('/kartu/<int:id_obat>')
def kartu_stok(id_obat):
    obat = Obat.query.get_or_404(id_obat)
    stok_list = Stok.query.filter_by(id_obat=id_obat).order_by(Stok.expired_date.asc()).all()
    # History adjustment
    adj_list = Adjustment.query.filter_by(id_obat=id_obat).order_by(Adjustment.tanggal.desc()).limit(50).all()
    from datetime import date as dt_date
    return render_template('kartu_stok.html', obat=obat, stok_list=stok_list, adj_list=adj_list, today=dt_date.today())


# ─── STOK MASUK ────────────────────────────────────────

@stok_bp.route('/masuk', methods=['GET', 'POST'])
def stok_masuk():
    if request.method == 'POST':
        id_obat = int(request.form['id_obat'])
        jumlah = int(request.form.get('jumlah', 0))
        batch = request.form.get('batch_number', '').strip()
        expired = request.form.get('expired_date')
        if jumlah <= 0:
            flash('Jumlah harus lebih dari 0!', 'error')
            return redirect(url_for('stok.stok_masuk'))
        expired_date = None
        if expired:
            expired_date = datetime.strptime(expired, '%Y-%m-%d').date()
        stok = Stok(
            id_obat=id_obat, batch_number=batch,
            expired_date=expired_date, jumlah=jumlah
        )
        db.session.add(stok)
        # Catat adjustment
        obat = Obat.query.get(id_obat)
        adj = Adjustment(
            id_obat=id_obat, jumlah_sebelum=0,
            jumlah_sesudah=jumlah, selisih=jumlah,
            alasan=f'Stok masuk - batch {batch}', id_user=session.get('user_id')
        )
        db.session.add(adj)
        db.session.commit()
        flash(f'Stok {obat.nama_generik if obat else ""} berhasil ditambahkan!', 'success')
        return redirect(url_for('stok.stok_index'))
    obat_list = Obat.query.filter_by(is_active=True).order_by(Obat.nama_generik).all()
    return render_template('stok_masuk.html', obat_list=obat_list)


# ─── STOK OPNAME ──────────────────────────────────────

@stok_bp.route('/opname', methods=['GET', 'POST'])
def stok_opname():
    if request.method == 'POST':
        data = request.form
        for key in data:
            if key.startswith('stok_fisik_'):
                id_stok = int(key.replace('stok_fisik_', ''))
                stok_baris = Stok.query.get(id_stok)
                if stok_baris:
                    fisik = int(data[key])
                    if fisik != stok_baris.jumlah:
                        selisih = fisik - stok_baris.jumlah
                        adj = Adjustment(
                            id_obat=stok_baris.id_obat, id_stok=id_stok,
                            jumlah_sebelum=stok_baris.jumlah,
                            jumlah_sesudah=fisik, selisih=selisih,
                            alasan=f'Opname: {stok_baris.jumlah} → {fisik}',
                            id_user=session.get('user_id')
                        )
                        stok_baris.jumlah = fisik
                        db.session.add(adj)
        db.session.commit()
        flash('Stok opname selesai!', 'success')
        return redirect(url_for('stok.stok_index'))

    # Tampilkan semua stok untuk opname
    all_stok = Stok.query.filter(Stok.jumlah > 0).order_by(Stok.expired_date.asc()).all()
    return render_template('stok_opname.html', all_stok=all_stok)
