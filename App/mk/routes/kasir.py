from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date
from models import db, Transaksi, DetailTransaksi, Obat, Stok, Pelanggan, Shift, Resep

kasir_bp = Blueprint('kasir', __name__, url_prefix='/kasir')


@kasir_bp.before_request
def check_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))


def buat_transaksi(detail_items, id_resep=None, id_pelanggan=None):
    """Helper untuk membuat transaksi"""
    max_id = db.session.query(db.func.max(Transaksi.id_transaksi)).scalar() or 0
    no_trans = f"TRX{datetime.now().strftime('%y%m%d')}{max_id + 1:04d}"

    subtotal = 0
    diskon_item_total = 0

    t = Transaksi(
        no_transaksi=no_trans,
        id_resep=id_resep,
        id_pelanggan=id_pelanggan,
        id_user=session.get('user_id'),
        id_shift=session.get('shift_id'),
        status='selesai'
    )
    db.session.add(t)
    db.session.flush()

    for item in detail_items:
        id_obat = item['id_obat']
        jumlah = item['jumlah']
        harga = item.get('harga', 0)
        diskon_item = item.get('diskon', 0)

        # FEFO: ambil dari batch expired terdekat
        sisa = jumlah
        batches = Stok.query.filter(
            Stok.id_obat == id_obat, Stok.jumlah > 0
        ).order_by(Stok.expired_date.asc().nullslast()).all()

        for batch in batches:
            if sisa <= 0:
                break
            ambil = min(sisa, batch.jumlah)
            sub = ambil * harga * (1 - diskon_item / 100)
            dt = DetailTransaksi(
                id_transaksi=t.id_transaksi,
                id_obat=id_obat,
                id_stok=batch.id_stok,
                jumlah=ambil,
                harga_jual=harga,
                diskon=diskon_item,
                subtotal=sub
            )
            db.session.add(dt)
            batch.jumlah -= ambil
            sisa -= ambil
            subtotal += sub
            diskon_item_total += sub * diskon_item / 100

    t.subtotal = subtotal
    t.diskon_item = diskon_item_total
    t.total = subtotal
    t.bayar = subtotal
    t.kembalian = 0

    # Update shift total
    if session.get('shift_id'):
        shift = Shift.query.get(session['shift_id'])
        if shift:
            shift.total_penjualan = (shift.total_penjualan or 0) + t.total

    db.session.commit()
    return t


@kasir_bp.route('/')
def kasir_index():
    shift_aktif = None
    if session.get('shift_id'):
        shift_aktif = Shift.query.get(session['shift_id'])

    # Transaksi hari ini
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    transaksi_hari = Transaksi.query.filter(
        Transaksi.tanggal >= today_start,
        Transaksi.status == 'selesai'
    ).order_by(Transaksi.tanggal.desc()).limit(20).all()

    return render_template('kasir_index.html',
        shift_aktif=shift_aktif,
        transaksi_hari=transaksi_hari,
        today=date.today()
    )


@kasir_bp.route('/shift/buka', methods=['POST'])
def shift_buka():
    if session.get('shift_id'):
        flash('Shift sudah dibuka!', 'error')
        return redirect(url_for('kasir.kasir_index'))

    saldo = float(request.form.get('saldo_awal', 0))
    shift = Shift(
        id_user=session.get('user_id'),
        saldo_awal=saldo
    )
    db.session.add(shift)
    db.session.flush()
    session['shift_id'] = shift.id_shift
    db.session.commit()
    flash('Shift berhasil dibuka!', 'success')
    return redirect(url_for('kasir.kasir_index'))


@kasir_bp.route('/shift/tutup', methods=['POST'])
def shift_tutup():
    if not session.get('shift_id'):
        flash('Tidak ada shift aktif!', 'error')
        return redirect(url_for('kasir.kasir_index'))
    shift = Shift.query.get(session['shift_id'])
    if shift:
        saldo_akhir = float(request.form.get('saldo_akhir', 0))
        shift.waktu_tutup = datetime.now()
        shift.saldo_akhir = saldo_akhir
        shift.selisih = saldo_akhir - shift.saldo_awal - shift.total_penjualan
        shift.status = 'tutup'
        db.session.commit()
        session.pop('shift_id', None)
        flash(f'Shift ditutup! Penjualan: Rp {shift.total_penjualan:,.0f}, Selisih: Rp {shift.selisih:,.0f}', 'success')
    return redirect(url_for('kasir.kasir_index'))


@kasir_bp.route('/transaksi-baru', methods=['POST'])
def transaksi_baru():
    if not session.get('shift_id'):
        flash('Buka shift kasir dulu!', 'error')
        return redirect(url_for('kasir.kasir_index'))

    data = request.form
    obat_ids = data.getlist('id_obat[]')
    jmls = data.getlist('jumlah[]')
    id_pelanggan = data.get('id_pelanggan', type=int) or None
    bayar = float(data.get('bayar', 0))
    diskon_global = float(data.get('diskon_global', 0))

    detail_items = []
    for i in range(len(obat_ids)):
        if not obat_ids[i].strip():
            continue
        id_obat = int(obat_ids[i])
        jumlah = int(jmls[i] or 0)
        if jumlah <= 0:
            continue
        obat = Obat.query.get(id_obat)
        if not obat or obat.stok_total < jumlah:
            flash(f'Stok {obat.nama_generik if obat else "?"} tidak mencukupi!', 'error')
            return redirect(url_for('kasir.kasir_index'))
        detail_items.append({
            'id_obat': id_obat,
            'jumlah': jumlah,
            'harga': obat.harga_jual_eceran
        })

    if not detail_items:
        flash('Tidak ada item dalam transaksi!', 'error')
        return redirect(url_for('kasir.kasir_index'))

    t = buat_transaksi(detail_items, id_pelanggan=id_pelanggan)

    # Apply diskon global
    if diskon_global > 0:
        t.diskon_global = diskon_global
        t.total = t.subtotal - diskon_global
    t.bayar = bayar
    t.kembalian = max(0, bayar - t.total)
    db.session.commit()

    flash(f'Transaksi #{t.no_transaksi} selesai! Kembalian: Rp {t.kembalian:,.0f}', 'success')
    return redirect(url_for('kasir.kasir_detail', id=t.id_transaksi))


@kasir_bp.route('/transaksi/<int:id>')
def kasir_detail(id):
    t = Transaksi.query.get_or_404(id)
    return render_template('kasir_detail.html', trx=t)


@kasir_bp.route('/transaksi/<int:id>/struk')
def kasir_struk(id):
    t = Transaksi.query.get_or_404(id)
    return render_template('kasir_struk.html', trx=t)


@kasir_bp.route('/transaksi/<int:id>/void', methods=['POST'])
def kasir_void(id):
    t = Transaksi.query.get_or_404(id)
    if t.status == 'void':
        flash('Transaksi sudah di-void!', 'error')
        return redirect(url_for('kasir.kasir_index'))

    t.status = 'void'
    # Kembalikan stok
    for dt in t.details.all():
        if dt.stok_batch:
            dt.stok_batch.jumlah += dt.jumlah
    db.session.commit()
    flash(f'Transaksi #{t.no_transaksi} di-void. Stok dikembalikan.', 'success')
    return redirect(url_for('kasir.kasir_index'))
