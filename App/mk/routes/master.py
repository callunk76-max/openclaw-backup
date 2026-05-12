from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from models import db, Obat, Kategori, Satuan, Supplier, Pelanggan, User

master_bp = Blueprint('master', __name__, url_prefix='/master')


def need_login():
    if not session.get('user_id'):
        return False
    return True


@master_bp.before_request
def check_login():
    if not need_login():
        return redirect(url_for('auth.login'))


# ─── OBAT ──────────────────────────────────────────────

@master_bp.route('/obat')
def obat_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    q = Obat.query
    if search:
        q = q.filter(db.or_(
            Obat.nama_generik.ilike(f'%{search}%'),
            Obat.nama_dagang.ilike(f'%{search}%'),
            Obat.kode_obat.ilike(f'%{search}%')
        ))
    q = q.order_by(Obat.id_obat.desc())
    pagination = q.paginate(page=page, per_page=25, error_out=False)
    kategori_list = Kategori.query.order_by(Kategori.nama_kategori).all()
    satuan_list = Satuan.query.order_by(Satuan.nama_satuan).all()
    return render_template('obat_list.html',
        pagination=pagination, obat_list=pagination.items,
        search=search, kategori_list=kategori_list, satuan_list=satuan_list)


@master_bp.route('/obat/tambah', methods=['GET', 'POST'])
def obat_tambah():
    if request.method == 'POST':
        max_id = db.session.query(db.func.max(Obat.id_obat)).scalar() or 0
        kode = f"OBT{max_id + 1:04d}"
        obat = Obat(
            kode_obat=kode,
            nama_generik=request.form['nama_generik'].strip(),
            nama_dagang=request.form.get('nama_dagang', '').strip(),
            id_kategori=int(request.form['id_kategori']) if request.form.get('id_kategori') else None,
            id_satuan=int(request.form['id_satuan']) if request.form.get('id_satuan') else None,
            golongan=request.form.get('golongan', 'Bebas'),
            harga_beli=float(request.form.get('harga_beli', 0) or 0),
            harga_jual_eceran=float(request.form.get('harga_jual_eceran', 0) or 0),
            harga_jual_resep=float(request.form.get('harga_jual_resep', 0) or 0),
            stok_minimum=int(request.form.get('stok_minimum', 0) or 0),
        )
        db.session.add(obat)
        db.session.commit()
        flash('Obat berhasil ditambahkan!', 'success')
        return redirect(url_for('master.obat_list'))
    kategori_list = Kategori.query.order_by(Kategori.nama_kategori).all()
    satuan_list = Satuan.query.order_by(Satuan.nama_satuan).all()
    return render_template('obat_form.html', obat=None, kategori_list=kategori_list, satuan_list=satuan_list)


@master_bp.route('/obat/<int:id>/edit', methods=['GET', 'POST'])
def obat_edit(id):
    obat = Obat.query.get_or_404(id)
    if request.method == 'POST':
        obat.nama_generik = request.form['nama_generik'].strip()
        obat.nama_dagang = request.form.get('nama_dagang', '').strip()
        obat.id_kategori = int(request.form['id_kategori']) if request.form.get('id_kategori') else None
        obat.id_satuan = int(request.form['id_satuan']) if request.form.get('id_satuan') else None
        obat.golongan = request.form.get('golongan', 'Bebas')
        obat.harga_beli = float(request.form.get('harga_beli', 0) or 0)
        obat.harga_jual_eceran = float(request.form.get('harga_jual_eceran', 0) or 0)
        obat.harga_jual_resep = float(request.form.get('harga_jual_resep', 0) or 0)
        obat.stok_minimum = int(request.form.get('stok_minimum', 0) or 0)
        obat.is_active = 'is_active' in request.form
        obat.updated_at = datetime.now()
        db.session.commit()
        flash('Obat berhasil diupdate!', 'success')
        return redirect(url_for('master.obat_list'))
    kategori_list = Kategori.query.order_by(Kategori.nama_kategori).all()
    satuan_list = Satuan.query.order_by(Satuan.nama_satuan).all()
    return render_template('obat_form.html', obat=obat, kategori_list=kategori_list, satuan_list=satuan_list)


@master_bp.route('/obat/<int:id>/delete', methods=['POST'])
def obat_delete(id):
    obat = Obat.query.get_or_404(id)
    obat.is_active = False
    db.session.commit()
    flash('Obat dinonaktifkan!', 'success')
    return redirect(url_for('master.obat_list'))


@master_bp.route('/obat/search')
def obat_search():
    q = request.args.get('q', '')
    if len(q) < 1:
        return jsonify([])
    results = Obat.query.filter(
        Obat.is_active == True,
        db.or_(Obat.nama_generik.ilike(f'%{q}%'), Obat.nama_dagang.ilike(f'%{q}%'),
               Obat.kode_obat.ilike(f'%{q}%'))
    ).limit(20).all()
    data = [{'id': o.id_obat, 'text': f'{o.kode_obat} - {o.nama_generik} ({o.nama_dagang})',
             'harga_jual': o.harga_jual_eceran, 'stok': o.stok_total} for o in results]
    return jsonify(data)


# ─── SUPPLIER ──────────────────────────────────────────

@master_bp.route('/supplier')
def supplier_list():
    supplier_list = Supplier.query.order_by(Supplier.nama).all()
    return render_template('supplier_list.html', supplier_list=supplier_list)


@master_bp.route('/supplier/tambah', methods=['GET', 'POST'])
def supplier_tambah():
    if request.method == 'POST':
        s = Supplier(
            nama=request.form['nama'].strip(),
            alamat=request.form.get('alamat', '').strip(),
            kota=request.form.get('kota', '').strip(),
            telepon=request.form.get('telepon', '').strip(),
            email=request.form.get('email', '').strip(),
            npwp=request.form.get('npwp', '').strip(),
            syarat_bayar=request.form.get('syarat_bayar', 'Tunai'),
        )
        db.session.add(s)
        db.session.commit()
        flash('Supplier berhasil ditambahkan!', 'success')
        return redirect(url_for('master.supplier_list'))
    return render_template('supplier_form.html', supplier=None)


@master_bp.route('/supplier/<int:id>/edit', methods=['GET', 'POST'])
def supplier_edit(id):
    s = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        s.nama = request.form['nama'].strip()
        s.alamat = request.form.get('alamat', '').strip()
        s.kota = request.form.get('kota', '').strip()
        s.telepon = request.form.get('telepon', '').strip()
        s.email = request.form.get('email', '').strip()
        s.npwp = request.form.get('npwp', '').strip()
        s.syarat_bayar = request.form.get('syarat_bayar', 'Tunai')
        s.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Supplier berhasil diupdate!', 'success')
        return redirect(url_for('master.supplier_list'))
    return render_template('supplier_form.html', supplier=s)


# ─── PELANGGAN ─────────────────────────────────────────

@master_bp.route('/pelanggan')
def pelanggan_list():
    pelanggan_list = Pelanggan.query.order_by(Pelanggan.nama).all()
    return render_template('pelanggan_list.html', pelanggan_list=pelanggan_list)


@master_bp.route('/pelanggan/tambah', methods=['GET', 'POST'])
def pelanggan_tambah():
    if request.method == 'POST':
        from datetime import date
        max_id = db.session.query(db.func.max(Pelanggan.id_pelanggan)).scalar() or 0
        p = Pelanggan(
            kode_member=f"MBR{max_id + 1:04d}",
            nama=request.form['nama'].strip(),
            telepon=request.form.get('telepon', '').strip(),
            alamat=request.form.get('alamat', '').strip(),
        )
        tgl = request.form.get('tanggal_lahir')
        if tgl:
            from datetime import datetime as dt
            p.tanggal_lahir = dt.strptime(tgl, '%Y-%m-%d').date()
        db.session.add(p)
        db.session.commit()
        flash('Pelanggan berhasil ditambahkan!', 'success')
        return redirect(url_for('master.pelanggan_list'))
    return render_template('pelanggan_form.html', pelanggan=None)


@master_bp.route('/pelanggan/<int:id>/edit', methods=['GET', 'POST'])
def pelanggan_edit(id):
    p = Pelanggan.query.get_or_404(id)
    if request.method == 'POST':
        p.nama = request.form['nama'].strip()
        p.telepon = request.form.get('telepon', '').strip()
        p.alamat = request.form.get('alamat', '').strip()
        tgl = request.form.get('tanggal_lahir')
        if tgl:
            from datetime import datetime as dt
            p.tanggal_lahir = dt.strptime(tgl, '%Y-%m-%d').date()
        p.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Pelanggan berhasil diupdate!', 'success')
        return redirect(url_for('master.pelanggan_list'))
    return render_template('pelanggan_form.html', pelanggan=p)


# ─── USER ──────────────────────────────────────────────

@master_bp.route('/user')
def user_list():
    if session.get('user_role') not in ('super_admin', 'manajer'):
        flash('Akses ditolak!', 'error')
        return redirect(url_for('dashboard.index'))
    user_list = User.query.order_by(User.nama).all()
    return render_template('user_list.html', user_list=user_list)


@master_bp.route('/user/tambah', methods=['GET', 'POST'])
def user_tambah():
    if session.get('user_role') not in ('super_admin',):
        flash('Akses ditolak!', 'error')
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        u = User(
            nama=request.form['nama'].strip(),
            username=request.form['username'].strip(),
            role=request.form.get('role', 'kasir'),
            no_sipa=request.form.get('no_sipa', '').strip(),
        )
        u.set_password(request.form['password'])
        db.session.add(u)
        db.session.commit()
        flash('User berhasil ditambahkan!', 'success')
        return redirect(url_for('master.user_list'))
    return render_template('user_form.html', user=None)


@master_bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
def user_edit(id):
    if session.get('user_role') not in ('super_admin',):
        flash('Akses ditolak!', 'error')
        return redirect(url_for('dashboard.index'))
    u = User.query.get_or_404(id)
    if request.method == 'POST':
        u.nama = request.form['nama'].strip()
        u.username = request.form['username'].strip()
        u.role = request.form.get('role', 'kasir')
        u.no_sipa = request.form.get('no_sipa', '').strip()
        if request.form.get('password'):
            u.set_password(request.form['password'])
        u.is_active = 'is_active' in request.form
        db.session.commit()
        flash('User berhasil diupdate!', 'success')
        return redirect(url_for('master.user_list'))
    return render_template('user_form.html', user=u)


@master_bp.route('/kategori')
def kategori_list():
    kategori_list = Kategori.query.order_by(Kategori.nama_kategori).all()
    satuan_list = Satuan.query.order_by(Satuan.nama_satuan).all()
    return render_template('kategori_satuan.html', kategori_list=kategori_list, satuan_list=satuan_list)


@master_bp.route('/kategori/tambah', methods=['POST'])
def kategori_tambah():
    k = Kategori(nama_kategori=request.form['nama'].strip())
    db.session.add(k)
    db.session.commit()
    flash('Kategori ditambahkan!', 'success')
    return redirect(url_for('master.kategori_list'))


@master_bp.route('/kategori/<int:id>/delete', methods=['POST'])
def kategori_delete(id):
    k = Kategori.query.get_or_404(id)
    if Obat.query.filter_by(id_kategori=id).first():
        flash('Kategori tidak bisa dihapus, masih dipakai obat!', 'error')
    else:
        db.session.delete(k)
        db.session.commit()
        flash('Kategori dihapus!', 'success')
    return redirect(url_for('master.kategori_list'))


@master_bp.route('/satuan/tambah', methods=['POST'])
def satuan_tambah():
    s = Satuan(nama_satuan=request.form['nama'].strip(),
               singkatan=request.form.get('singkatan', '').strip())
    db.session.add(s)
    db.session.commit()
    flash('Satuan ditambahkan!', 'success')
    return redirect(url_for('master.kategori_list'))


@master_bp.route('/satuan/<int:id>/delete', methods=['POST'])
def satuan_delete(id):
    s = Satuan.query.get_or_404(id)
    if Obat.query.filter_by(id_satuan=id).first():
        flash('Satuan tidak bisa dihapus, masih dipakai obat!', 'error')
    else:
        db.session.delete(s)
        db.session.commit()
        flash('Satuan dihapus!', 'success')
    return redirect(url_for('master.kategori_list'))
