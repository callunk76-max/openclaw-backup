from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─── MASTER ────────────────────────────────────────────

class Obat(db.Model):
    __tablename__ = 'tbl_obat'
    id_obat = db.Column(db.Integer, primary_key=True)
    kode_obat = db.Column(db.String(20), unique=True, nullable=False)
    nama_generik = db.Column(db.String(200), nullable=False)
    nama_dagang = db.Column(db.String(200), default='')
    id_kategori = db.Column(db.Integer, db.ForeignKey('tbl_kategori.id_kategori'))
    id_satuan = db.Column(db.Integer, db.ForeignKey('tbl_satuan.id_satuan'))
    golongan = db.Column(db.String(20), default='Bebas')
    # Bebas / Bebas Terbatas / Keras / Narkotika / Psikotropika
    harga_beli = db.Column(db.Float, default=0)
    harga_jual_eceran = db.Column(db.Float, default=0)
    harga_jual_resep = db.Column(db.Float, default=0)
    stok_minimum = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    kategori = db.relationship('Kategori', backref='obat_list', lazy=True)
    satuan = db.relationship('Satuan', backref='obat_list', lazy=True)

    @property
    def stok_total(self):
        total = db.session.query(db.func.coalesce(db.func.sum(Stok.jumlah), 0))\
            .filter(Stok.id_obat == self.id_obat).scalar()
        return total or 0

    @property
    def stok_available(self):
        return self.stok_total

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Kategori(db.Model):
    __tablename__ = 'tbl_kategori'
    id_kategori = db.Column(db.Integer, primary_key=True)
    nama_kategori = db.Column(db.String(100), nullable=False, unique=True)
    deskripsi = db.Column(db.Text, default='')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Satuan(db.Model):
    __tablename__ = 'tbl_satuan'
    id_satuan = db.Column(db.Integer, primary_key=True)
    nama_satuan = db.Column(db.String(50), nullable=False, unique=True)
    singkatan = db.Column(db.String(10), default='')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Supplier(db.Model):
    __tablename__ = 'tbl_supplier'
    id_supplier = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200), nullable=False)
    alamat = db.Column(db.Text, default='')
    kota = db.Column(db.String(100), default='')
    telepon = db.Column(db.String(30), default='')
    email = db.Column(db.String(100), default='')
    npwp = db.Column(db.String(30), default='')
    syarat_bayar = db.Column(db.String(50), default='Tunai')
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Pelanggan(db.Model):
    __tablename__ = 'tbl_pelanggan'
    id_pelanggan = db.Column(db.Integer, primary_key=True)
    kode_member = db.Column(db.String(20), unique=True)
    nama = db.Column(db.String(200), nullable=False)
    telepon = db.Column(db.String(30), default='')
    alamat = db.Column(db.Text, default='')
    tanggal_lahir = db.Column(db.Date, nullable=True)
    total_poin = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(db.Model):
    __tablename__ = 'tbl_user'
    id_user = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), default='kasir')
    # super_admin, apoteker, ttk, kasir, gudang, manajer
    no_sipa = db.Column(db.String(50), default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != 'password_hash'}


# ─── STOK ─────────────────────────────────────────────

class Stok(db.Model):
    __tablename__ = 'tbl_stok'
    id_stok = db.Column(db.Integer, primary_key=True)
    id_obat = db.Column(db.Integer, db.ForeignKey('tbl_obat.id_obat'), nullable=False)
    batch_number = db.Column(db.String(50), default='')
    expired_date = db.Column(db.Date, nullable=True)
    jumlah = db.Column(db.Integer, default=0)
    id_pembelian = db.Column(db.Integer, db.ForeignKey('tbl_pembelian.id_pembelian'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    obat = db.relationship('Obat', backref='stok_list', lazy=True)
    pembelian = db.relationship('Pembelian', backref='stok_list', lazy=True)


class Adjustment(db.Model):
    __tablename__ = 'tbl_adjustment'
    id_adj = db.Column(db.Integer, primary_key=True)
    id_obat = db.Column(db.Integer, db.ForeignKey('tbl_obat.id_obat'), nullable=False)
    id_stok = db.Column(db.Integer, db.ForeignKey('tbl_stok.id_stok'), nullable=True)
    jumlah_sebelum = db.Column(db.Integer, default=0)
    jumlah_sesudah = db.Column(db.Integer, default=0)
    selisih = db.Column(db.Integer, default=0)
    alasan = db.Column(db.Text, default='')
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'), nullable=True)
    tanggal = db.Column(db.DateTime, default=datetime.now)

    obat = db.relationship('Obat', backref='adjustments', lazy=True)
    user = db.relationship('User', backref='adjustments', lazy=True)


# ─── PEMBELIAN ─────────────────────────────────────────

class Pembelian(db.Model):
    __tablename__ = 'tbl_pembelian'
    id_pembelian = db.Column(db.Integer, primary_key=True)
    no_po = db.Column(db.String(30), unique=True, nullable=False)
    id_supplier = db.Column(db.Integer, db.ForeignKey('tbl_supplier.id_supplier'), nullable=False)
    tanggal_po = db.Column(db.Date, default=date.today)
    tanggal_terima = db.Column(db.Date, nullable=True)
    total = db.Column(db.Float, default=0)
    diskon = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='draft')
    # draft, dikirim, sebagian, selesai, batal
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'), nullable=True)
    catatan = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.now)

    supplier = db.relationship('Supplier', backref='pembelian_list', lazy=True)
    user = db.relationship('User', backref='pembelian_list', lazy=True)
    details = db.relationship('DetailPembelian', backref='pembelian', lazy='dynamic',
                              cascade='all, delete-orphan')


class DetailPembelian(db.Model):
    __tablename__ = 'tbl_detail_pembelian'
    id = db.Column(db.Integer, primary_key=True)
    id_pembelian = db.Column(db.Integer, db.ForeignKey('tbl_pembelian.id_pembelian'), nullable=False)
    id_obat = db.Column(db.Integer, db.ForeignKey('tbl_obat.id_obat'), nullable=False)
    jumlah_pesan = db.Column(db.Integer, default=0)
    jumlah_terima = db.Column(db.Integer, nullable=True)
    harga_beli = db.Column(db.Float, default=0)
    diskon_persen = db.Column(db.Float, default=0)
    batch_number = db.Column(db.String(50), default='')
    expired_date = db.Column(db.Date, nullable=True)
    subtotal = db.Column(db.Float, default=0)

    obat = db.relationship('Obat', backref='detail_pembelian', lazy=True)


class HutangSupplier(db.Model):
    __tablename__ = 'tbl_hutang_supplier'
    id_hutang = db.Column(db.Integer, primary_key=True)
    id_pembelian = db.Column(db.Integer, db.ForeignKey('tbl_pembelian.id_pembelian'), nullable=False)
    no_faktur = db.Column(db.String(50), default='')
    tanggal_faktur = db.Column(db.Date, nullable=True)
    jatuh_tempo = db.Column(db.Date, nullable=True)
    total = db.Column(db.Float, default=0)
    sisa = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='belum')
    # belum, sebagian, lunas

    pembelian = db.relationship('Pembelian', backref='hutang', lazy=True)
    bayar_list = db.relationship('BayarHutang', backref='hutang', lazy='dynamic',
                                 cascade='all, delete-orphan')


class BayarHutang(db.Model):
    __tablename__ = 'tbl_bayar_hutang'
    id_bayar = db.Column(db.Integer, primary_key=True)
    id_hutang = db.Column(db.Integer, db.ForeignKey('tbl_hutang_supplier.id_hutang'), nullable=False)
    tanggal = db.Column(db.Date, default=date.today)
    jumlah = db.Column(db.Float, default=0)
    metode = db.Column(db.String(50), default='Tunai')
    keterangan = db.Column(db.Text, default='')
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'), nullable=True)

    user = db.relationship('User', backref='bayar_hutang', lazy=True)


# ─── RESEP ─────────────────────────────────────────────

class Resep(db.Model):
    __tablename__ = 'tbl_resep'
    id_resep = db.Column(db.Integer, primary_key=True)
    no_resep = db.Column(db.String(30), unique=True, nullable=False)
    nama_dokter = db.Column(db.String(100), default='')
    nama_pasien = db.Column(db.String(100), nullable=False)
    id_pelanggan = db.Column(db.Integer, db.ForeignKey('tbl_pelanggan.id_pelanggan'), nullable=True)
    tanggal = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='masuk')
    # masuk, diproses, siap, selesai
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'), nullable=True)
    catatan = db.Column(db.Text, default='')

    pelanggan = db.relationship('Pelanggan', backref='resep_list', lazy=True)
    user = db.relationship('User', backref='resep_list', lazy=True)
    details = db.relationship('DetailResep', backref='resep', lazy='dynamic',
                              cascade='all, delete-orphan')


class DetailResep(db.Model):
    __tablename__ = 'tbl_detail_resep'
    id = db.Column(db.Integer, primary_key=True)
    id_resep = db.Column(db.Integer, db.ForeignKey('tbl_resep.id_resep'), nullable=False)
    id_obat = db.Column(db.Integer, db.ForeignKey('tbl_obat.id_obat'), nullable=False)
    jumlah = db.Column(db.Integer, default=0)
    aturan_pakai = db.Column(db.Text, default='')
    signa = db.Column(db.String(50), default='')
    keterangan = db.Column(db.Text, default='')

    obat = db.relationship('Obat', backref='detail_resep', lazy=True)


# ─── TRANSAKSI / KASIR ─────────────────────────────────

class Transaksi(db.Model):
    __tablename__ = 'tbl_transaksi'
    id_transaksi = db.Column(db.Integer, primary_key=True)
    no_transaksi = db.Column(db.String(30), unique=True, nullable=False)
    id_resep = db.Column(db.Integer, db.ForeignKey('tbl_resep.id_resep'), nullable=True)
    id_pelanggan = db.Column(db.Integer, db.ForeignKey('tbl_pelanggan.id_pelanggan'), nullable=True)
    tanggal = db.Column(db.DateTime, default=datetime.now)
    subtotal = db.Column(db.Float, default=0)
    diskon_item = db.Column(db.Float, default=0)
    diskon_global = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    bayar = db.Column(db.Float, default=0)
    kembalian = db.Column(db.Float, default=0)
    metode_bayar = db.Column(db.String(50), default='Tunai')
    poin_dipakai = db.Column(db.Integer, default=0)
    poin_didapat = db.Column(db.Integer, default=0)
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'), nullable=True)
    id_shift = db.Column(db.Integer, db.ForeignKey('tbl_shift.id_shift'), nullable=True)
    status = db.Column(db.String(20), default='selesai')

    resep = db.relationship('Resep', backref='transaksi', lazy=True)
    pelanggan = db.relationship('Pelanggan', backref='transaksi_list', lazy=True)
    user = db.relationship('User', backref='transaksi_list', lazy=True)
    shift = db.relationship('Shift', backref='transaksi_list', lazy=True)
    details = db.relationship('DetailTransaksi', backref='transaksi', lazy='dynamic',
                              cascade='all, delete-orphan')


class DetailTransaksi(db.Model):
    __tablename__ = 'tbl_detail_transaksi'
    id = db.Column(db.Integer, primary_key=True)
    id_transaksi = db.Column(db.Integer, db.ForeignKey('tbl_transaksi.id_transaksi'), nullable=False)
    id_obat = db.Column(db.Integer, db.ForeignKey('tbl_obat.id_obat'), nullable=False)
    id_stok = db.Column(db.Integer, db.ForeignKey('tbl_stok.id_stok'), nullable=True)
    jumlah = db.Column(db.Integer, default=0)
    harga_jual = db.Column(db.Float, default=0)
    diskon = db.Column(db.Float, default=0)
    subtotal = db.Column(db.Float, default=0)

    obat = db.relationship('Obat', backref='detail_transaksi', lazy=True)
    stok_batch = db.relationship('Stok', backref='detail_transaksi', lazy=True)


class Shift(db.Model):
    __tablename__ = 'tbl_shift'
    id_shift = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'), nullable=False)
    waktu_buka = db.Column(db.DateTime, default=datetime.now)
    waktu_tutup = db.Column(db.DateTime, nullable=True)
    saldo_awal = db.Column(db.Float, default=0)
    total_penjualan = db.Column(db.Float, default=0)
    saldo_akhir = db.Column(db.Float, nullable=True)
    selisih = db.Column(db.Float, default=0)
    status = db.Column(db.String(10), default='buka')

    user = db.relationship('User', backref='shift_list', lazy=True)


# ─── LOG ───────────────────────────────────────────────

class AuditLog(db.Model):
    __tablename__ = 'tbl_audit_log'
    id_log = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'), nullable=True)
    aksi = db.Column(db.String(100), nullable=False)
    tabel = db.Column(db.String(50), nullable=False)
    id_record = db.Column(db.Integer, nullable=True)
    data_lama = db.Column(db.Text, nullable=True)
    data_baru = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), default='')
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref='audit_logs', lazy=True)
