from flask import Blueprint, render_template, request, session, redirect, url_for
from datetime import datetime, date, timedelta
from models import db, Transaksi, DetailTransaksi, Obat, Resep, Pelanggan, User, Shift

laporan_bp = Blueprint('laporan', __name__, url_prefix='/laporan')


@laporan_bp.before_request
def check_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))


@laporan_bp.route('/')
def laporan_index():
    today = date.today()
    start = request.args.get('start', today.replace(day=1).isoformat())
    end = request.args.get('end', today.isoformat())

    try:
        start_dt = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)
    except:
        start_dt = today.replace(day=1)
        end_dt = today + timedelta(days=1)

    transaksi = Transaksi.query.filter(
        Transaksi.tanggal >= start_dt,
        Transaksi.tanggal < end_dt,
        Transaksi.status == 'selesai'
    ).order_by(Transaksi.tanggal.desc()).all()

    total_penjualan = sum(t.total for t in transaksi)
    total_item = sum(len(list(t.details)) for t in transaksi)
    jumlah_trx = len(transaksi)

    # Per metode bayar
    metode = {}
    for t in transaksi:
        m = t.metode_bayar or 'Tunai'
        metode[m] = metode.get(m, 0) + t.total

    # Per user/kasir
    per_kasir = {}
    for t in transaksi:
        kasir = t.user.nama if t.user else 'Unknown'
        per_kasir[kasir] = per_kasir.get(kasir, 0) + t.total

    # Top obat
    obat_terjual = {}
    for t in transaksi:
        for dt in t.details.all():
            nama = dt.obat.nama_generik if dt.obat else f"ID:{dt.id_obat}"
            obat_terjual[nama] = obat_terjual.get(nama, 0) + dt.jumlah

    top_obat = sorted(obat_terjual.items(), key=lambda x: x[1], reverse=True)[:20]

    return render_template('laporan_index.html',
        start=start, end=end,
        total_penjualan=total_penjualan,
        jumlah_trx=jumlah_trx,
        total_item=total_item,
        transaksi=transaksi,
        metode=metode,
        per_kasir=per_kasir,
        top_obat=top_obat
    )


@ laporan_bp.route('/stok')
def laporan_stok():
    from models import Stok, Adjustment, Kategori
    today = date.today()
    tiga_bulan = today + timedelta(days=90)

    # Stok menipis
    menipis = []
    for o in Obat.query.filter_by(is_active=True).all():
        if o.stok_total <= o.stok_minimum:
            menipis.append(o)

    # Expired
    expired = db.session.query(Obat, Stok).join(Stok).filter(
        Stok.expired_date != None,
        Stok.expired_date <= tiga_bulan,
        Stok.jumlah > 0
    ).order_by(Stok.expired_date).all()

    return render_template('laporan_stok.html',
        menipis=menipis, expired=expired, today=today, tiga_bulan=tiga_bulan
    )


@ laporan_bp.route('/shift')
def laporan_shift():
    shifts = Shift.query.order_by(Shift.waktu_buka.desc()).limit(50).all()
    return render_template('laporan_shift.html', shifts=shifts)
