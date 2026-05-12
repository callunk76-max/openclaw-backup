from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, date
from models import db, Pembelian, DetailPembelian, Supplier, Obat, Stok, HutangSupplier, BayarHutang, User

pembelian_bp = Blueprint('pembelian', __name__, url_prefix='/pembelian')


@pembelian_bp.before_request
def check_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))


@pembelian_bp.route('/')
def pembelian_list():
    page = request.args.get('page', 1, type=int)
    pagination = Pembelian.query.order_by(Pembelian.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('pembelian_list.html', pagination=pagination, list=pagination.items)


@pembelian_bp.route('/tambah', methods=['GET', 'POST'])
def pembelian_tambah():
    if request.method == 'POST':
        max_id = db.session.query(db.func.max(Pembelian.id_pembelian)).scalar() or 0
        no_po = f"PO{datetime.now().strftime('%y%m')}{max_id + 1:04d}"
        p = Pembelian(
            no_po=no_po,
            id_supplier=int(request.form['id_supplier']),
            tanggal_po=datetime.strptime(request.form['tanggal_po'], '%Y-%m-%d').date(),
            status='draft',
            id_user=session.get('user_id'),
            catatan=request.form.get('catatan', '')
        )
        db.session.add(p)
        db.session.flush()

        # Process items
        obat_ids = request.form.getlist('id_obat[]')
        jml_pesan = request.form.getlist('jumlah_pesan[]')
        hrg_beli = request.form.getlist('harga_beli[]')
        diskon = request.form.getlist('diskon_persen[]')
        batch_nums = request.form.getlist('batch_number[]')
        exp_dates = request.form.getlist('expired_date[]')

        total = 0
        for i in range(len(obat_ids)):
            if not obat_ids[i].strip():
                continue
            harga = float(hrg_beli[i] or 0)
            jml = int(jml_pesan[i] or 0)
            dsc = float(diskon[i] or 0)
            subtotal = (harga * jml) * (1 - dsc / 100)
            total += subtotal
            exp_date = None
            if exp_dates[i] and exp_dates[i].strip():
                exp_date = datetime.strptime(exp_dates[i], '%Y-%m-%d').date()
            dp = DetailPembelian(
                id_pembelian=p.id_pembelian,
                id_obat=int(obat_ids[i]),
                jumlah_pesan=jml,
                harga_beli=harga,
                diskon_persen=dsc,
                batch_number=batch_nums[i] if batch_nums else '',
                expired_date=exp_date,
                subtotal=subtotal
            )
            db.session.add(dp)

        p.total = total
        db.session.commit()
        flash(f'PO {no_po} berhasil dibuat!', 'success')
        return redirect(url_for('pembelian.pembelian_list'))

    supplier_list = Supplier.query.filter_by(is_active=True).order_by(Supplier.nama).all()
    obat_list = Obat.query.filter_by(is_active=True).order_by(Obat.nama_generik).all()
    today_str = date.today().isoformat()
    return render_template('pembelian_form.html', supplier_list=supplier_list, obat_list=obat_list, today=today_str)


@pembelian_bp.route('/<int:id>/terima', methods=['POST'])
def pembelian_terima(id):
    p = Pembelian.query.get_or_404(id)
    p.status = 'selesai'
    p.tanggal_terima = date.today()
    for dp in p.details.all():
        dp.jumlah_terima = request.form.get(f'jml_terima_{dp.id}', type=int) or dp.jumlah_pesan
        if dp.jumlah_terima > 0:
            stok = Stok(
                id_obat=dp.id_obat, batch_number=dp.batch_number,
                expired_date=dp.expired_date, jumlah=dp.jumlah_terima,
                id_pembelian=p.id_pembelian
            )
            db.session.add(stok)
    db.session.commit()
    flash('Penerimaan barang berhasil! Stok otomatis bertambah.', 'success')
    return redirect(url_for('pembelian.pembelian_list'))


@pembelian_bp.route('/<int:id>/batal', methods=['POST'])
def pembelian_batal(id):
    p = Pembelian.query.get_or_404(id)
    p.status = 'batal'
    db.session.commit()
    flash('PO dibatalkan!', 'success')
    return redirect(url_for('pembelian.pembelian_list'))


# ─── HUTANG ──────────────────────────────────────────

@pembelian_bp.route('/hutang')
def hutang_list():
    hutang_list = HutangSupplier.query.order_by(HutangSupplier.jatuh_tempo.asc()).all()
    return render_template('hutang_list.html', hutang_list=hutang_list)


@pembelian_bp.route('/hutang/bayar/<int:id>', methods=['POST'])
def hutang_bayar(id):
    hutang = HutangSupplier.query.get_or_404(id)
    jumlah = float(request.form.get('jumlah', 0))
    metode = request.form.get('metode', 'Tunai')
    if jumlah <= 0 or jumlah > hutang.sisa:
        flash('Jumlah pembayaran tidak valid!', 'error')
        return redirect(url_for('pembelian.hutang_list'))
    bayar = BayarHutang(
        id_hutang=id, tanggal=date.today(),
        jumlah=jumlah, metode=metode,
        id_user=session.get('user_id')
    )
    db.session.add(bayar)
    hutang.sisa -= jumlah
    hutang.status = 'lunas' if hutang.sisa <= 0 else 'sebagian'
    db.session.commit()
    flash(f'Pembayaran Rp {jumlah:,.0f} berhasil!', 'success')
    return redirect(url_for('pembelian.hutang_list'))
