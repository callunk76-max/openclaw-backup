from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date
from models import db, Resep, DetailResep, Obat, Pelanggan, Stok, Transaksi, DetailTransaksi

resep_bp = Blueprint('resep', __name__, url_prefix='/resep')


@resep_bp.before_request
def check_login():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))


@resep_bp.route('/')
def resep_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    q = Resep.query
    if search:
        q = q.filter(db.or_(
            Resep.nama_pasien.ilike(f'%{search}%'),
            Resep.no_resep.ilike(f'%{search}%'),
            Resep.nama_dokter.ilike(f'%{search}%')
        ))
    if status:
        q = q.filter(Resep.status == status)
    pagination = q.order_by(Resep.tanggal.desc()).paginate(page=page, per_page=20, error_out=False)
    status_list = ['masuk', 'diproses', 'siap', 'selesai']
    return render_template('resep_list.html', pagination=pagination, list=pagination.items,
                           status_list=status_list, search=search, cur_status=status)


@resep_bp.route('/tambah', methods=['GET', 'POST'])
def resep_tambah():
    if request.method == 'POST':
        today_seq = Resep.query.filter(db.func.date(Resep.tanggal) == date.today()).count() + 1
        no_resep = f"RX{date.today().strftime('%d%m%y')}{today_seq:03d}"
        id_pel = request.form.get('id_pelanggan')
        r = Resep(
            no_resep=no_resep,
            nama_dokter=request.form.get('nama_dokter', '').strip(),
            nama_pasien=request.form['nama_pasien'].strip(),
            id_pelanggan=int(id_pel) if id_pel else None,
            id_user=session.get('user_id'),
            catatan=request.form.get('catatan', '')
        )
        db.session.add(r)
        db.session.flush()

        obat_ids = request.form.getlist('id_obat[]')
        jmls = request.form.getlist('jumlah[]')
        aturans = request.form.getlist('aturan_pakai[]')
        signas = request.form.getlist('signa[]')

        for i in range(len(obat_ids)):
            if not obat_ids[i].strip():
                continue
            dr = DetailResep(
                id_resep=r.id_resep,
                id_obat=int(obat_ids[i]),
                jumlah=int(jmls[i] or 0),
                aturan_pakai=aturans[i] if aturans else '',
                signa=signas[i] if signas else ''
            )
            db.session.add(dr)
        db.session.commit()
        flash(f'Resep {no_resep} berhasil dicatat!', 'success')
        return redirect(url_for('resep.resep_list'))

    obat_list = Obat.query.filter_by(is_active=True).order_by(Obat.nama_generik).all()
    return render_template('resep_form.html', obat_list=obat_list)


@resep_bp.route('/<int:id>/status', methods=['POST'])
def resep_status(id):
    r = Resep.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ('masuk', 'diproses', 'siap', 'selesai'):
        r.status = new_status
        if new_status == 'selesai':
            # Kurangi stok otomatis
            for dr in r.details.all():
                sisa = dr.jumlah
                batches = Stok.query.filter(
                    Stok.id_obat == dr.id_obat, Stok.jumlah > 0,
                    Stok.expired_date != None
                ).order_by(Stok.expired_date.asc()).all()
                for batch in batches:
                    if sisa <= 0:
                        break
                    ambil = min(sisa, batch.jumlah)
                    batch.jumlah -= ambil
                    sisa -= ambil
        db.session.commit()
        flash(f'Status resep: {new_status}!', 'success')
    return redirect(url_for('resep.resep_list'))


@resep_bp.route('/<int:id>/detail')
def resep_detail(id):
    r = Resep.query.get_or_404(id)
    return render_template('resep_detail.html', resep=r)


@resep_bp.route('/<int:id>/to-transaksi', methods=['POST'])
def resep_to_transaksi(id):
    r = Resep.query.get_or_404(id)
    if not session.get('shift_id'):
        flash('Buka shift kasir dulu!', 'error')
        return redirect(url_for('kasir.kasir_index'))

    # Buat transaksi dari resep
    from routes.kasir import buat_transaksi
    detail_items = []
    for dr in r.details.all():
        obat = Obat.query.get(dr.id_obat)
        detail_items.append({
            'id_obat': dr.id_obat,
            'jumlah': dr.jumlah,
            'harga': obat.harga_jual_resep if obat else 0
        })

    if detail_items:
        t = buat_transaksi(detail_items, id_resep=r.id_resep, id_pelanggan=r.id_pelanggan)
        flash(f'Transaksi #{t.no_transaksi} dari resep berhasil!', 'success')
        return redirect(url_for('kasir.kasir_detail', id=t.id_transaksi))
    return redirect(url_for('resep.resep_list'))


# ─── ETIKET ───────────────────────────────────────────

@resep_bp.route('/<int:id>/etiket')
def etiket(id):
    r = Resep.query.get_or_404(id)
    return render_template('etiket.html', resep=r)
