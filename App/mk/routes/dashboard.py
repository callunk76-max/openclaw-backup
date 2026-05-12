from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime, date, timedelta
from models import db, Obat, Stok, Transaksi, Resep, Pelanggan, User

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')


def login_required():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))


@dashboard_bp.route('/')
def index():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))

    today = date.today()
    first_of_month = today.replace(day=1)

    total_obat = Obat.query.count()
    total_pelanggan = Pelanggan.query.count()

    # Obat stok menipis (di bawah minimum)
    obat_menipis = []
    for obat in Obat.query.filter_by(is_active=True).all():
        if obat.stok_total <= obat.stok_minimum:
            obat_menipis.append(obat)
    obat_menipis = sorted(obat_menipis, key=lambda o: o.stok_total / max(o.stok_minimum, 1))[:10]

    # Obat expired dalam 3 bulan
    tiga_bln = today + timedelta(days=90)
    expired_obat = db.session.query(Obat, Stok).join(Stok, Stok.id_obat == Obat.id_obat)\
        .filter(Stok.expired_date != None, Stok.expired_date <= tiga_bln, Stok.expired_date >= today, Stok.jumlah > 0)\
        .order_by(Stok.expired_date.asc()).all()

    # Penjualan hari ini
    penjualan_hari_ini = Transaksi.query.filter(
        db.func.date(Transaksi.tanggal) == today,
        Transaksi.status == 'selesai'
    ).all()
    total_penjualan = sum(t.total for t in penjualan_hari_ini)
    jumlah_transaksi = len(penjualan_hari_ini)

    # Penjualan bulan ini
    penjualan_bulan = Transaksi.query.filter(
        Transaksi.tanggal >= first_of_month,
        Transaksi.status == 'selesai'
    ).all()
    total_bulan = sum(t.total for t in penjualan_bulan)

    # Resep hari ini
    resep_hari_ini = Resep.query.filter(
        db.func.date(Resep.tanggal) == today
    ).count()

    # Resep pending
    resep_pending = Resep.query.filter(Resep.status.in_(['masuk', 'diproses'])).count()

    return render_template('dashboard.html',
        total_obat=total_obat,
        total_pelanggan=total_pelanggan,
        obat_menipis=obat_menipis,
        expired_obat=expired_obat,
        total_penjualan=total_penjualan,
        jumlah_transaksi=jumlah_transaksi,
        total_bulan=total_bulan,
        resep_hari_ini=resep_hari_ini,
        resep_pending=resep_pending,
        today=today
    )
