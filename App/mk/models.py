"""Farmasi Puskesmas - Database Models"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

# ─── Referensi ───────────────────────────────────────────

class Desa(db.Model):
    __tablename__ = 'desa'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    kecamatan = db.Column(db.String(100), default='Ujung Loe')
    kabupaten = db.Column(db.String(100), default='Bulukumba')
    provinsi = db.Column(db.String(100), default='Sulawesi Selatan')

    pasien = db.relationship('Pasien', backref='desa', lazy=True)
    unit = db.relationship('UnitPelayanan', backref='desa', lazy=True)

    def __repr__(self): return self.nama


class KategoriItem(db.Model):
    __tablename__ = 'kategori_item'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    tipe = db.Column(db.String(10), nullable=False)  # 'obat' / 'bhp'

    items = db.relationship('ItemFarmasi', backref='kategori', lazy=True)
    def __repr__(self): return self.nama


# ─── Master Data ─────────────────────────────────────────

class ItemFarmasi(db.Model):
    __tablename__ = 'item_farmasi'
    id = db.Column(db.Integer, primary_key=True)
    kategori_id = db.Column(db.Integer, db.ForeignKey('kategori_item.id'))
    kode = db.Column(db.String(50))                    # e-katalog / KFA
    nama_generik = db.Column(db.String(200))
    nama_dagang = db.Column(db.String(200))
    bentuk = db.Column(db.String(50))                  # Tab, Kaps, Sir, Inj, Cream
    kekuatan = db.Column(db.String(50))                # 500 mg, 250 mg/5 mL
    satuan = db.Column(db.String(20))                  # tab, btl, box, pcs
    tipe = db.Column(db.String(10), nullable=False)    # 'obat' / 'bhp'
    golongan = db.Column(db.String(20), default='bebas')  # bebas, terbatas, narkotik, psikotropik
    fornas = db.Column(db.Boolean, default=True)
    racikan = db.Column(db.Boolean, default=False)
    harga_acuan = db.Column(db.Float)
    batas_min_stok = db.Column(db.Integer, default=10)
    aktif = db.Column(db.Boolean, default=True)

    stok = db.relationship('Stok', backref='item', lazy=True)
    def __repr__(self): return f"{self.nama_generik} {self.kekuatan or ''}"


class Dokter(db.Model):
    __tablename__ = 'dokter'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200), nullable=False)
    sip = db.Column(db.String(50))
    jenis = db.Column(db.String(30))                   # dokter, bidan, perawat, apoteker
    unit_id = db.Column(db.Integer, db.ForeignKey('unit_pelayanan.id'))
    aktif = db.Column(db.Boolean, default=True)

    def __repr__(self): return self.nama


# ─── Wilayah & Unit ──────────────────────────────────────

class UnitPelayanan(db.Model):
    __tablename__ = 'unit_pelayanan'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    tipe = db.Column(db.String(20), nullable=False)    # puskesmas, pustu, polindes, poskesdes
    alamat = db.Column(db.Text)
    desa_id = db.Column(db.Integer, db.ForeignKey('desa.id'))
    induk_id = db.Column(db.Integer, db.ForeignKey('unit_pelayanan.id'))
    rawat_inap = db.Column(db.Boolean, default=False)
    aktif = db.Column(db.Boolean, default=True)

    dokter = db.relationship('Dokter', backref='unit', lazy=True)
    stok = db.relationship('Stok', backref='unit', lazy=True)
    resep = db.relationship('Resep', backref='unit', lazy=True)

    def __repr__(self): return self.nama


class Pasien(db.Model):
    __tablename__ = 'pasien'
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(16))
    no_bpjs = db.Column(db.String(20))
    nama = db.Column(db.String(200), nullable=False)
    jenis_kelamin = db.Column(db.String(1))
    tempat_lahir = db.Column(db.String(100))
    tanggal_lahir = db.Column(db.Date)
    alamat = db.Column(db.Text)
    desa_id = db.Column(db.Integer, db.ForeignKey('desa.id'))
    telepon = db.Column(db.String(20))
    pekerjaan = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    resep = db.relationship('Resep', backref='pasien', lazy=True)


# ─── Resep & Racikan ─────────────────────────────────────

class Resep(db.Model):
    __tablename__ = 'resep'
    id = db.Column(db.Integer, primary_key=True)
    no_resep = db.Column(db.String(30), unique=True)
    tanggal = db.Column(db.Date, default=date.today)
    jenis_pelayanan = db.Column(db.String(10), default='RAWAT_JALAN')
    no_rm = db.Column(db.String(20))
    no_kamar = db.Column(db.String(20))
    pasien_id = db.Column(db.Integer, db.ForeignKey('pasien.id'))
    dokter_id = db.Column(db.Integer, db.ForeignKey('dokter.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit_pelayanan.id'))
    keluhan = db.Column(db.Text)
    jaminan = db.Column(db.String(20), default='BPJS')
    no_sep = db.Column(db.String(30))
    status = db.Column(db.String(20), default='baru')
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    items = db.relationship('ResepItem', backref='resep', lazy=True, cascade='all,delete')
    racikan = db.relationship('Racikan', backref='resep', lazy=True, cascade='all,delete')

    def total_obat(self):
        return sum(i.qty for i in self.items)


class ResepItem(db.Model):
    __tablename__ = 'resep_item'
    id = db.Column(db.Integer, primary_key=True)
    resep_id = db.Column(db.Integer, db.ForeignKey('resep.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item_farmasi.id'))
    racikan_id = db.Column(db.Integer, db.ForeignKey('racikan.id'), nullable=True)
    qty = db.Column(db.Float, default=1)
    aturan = db.Column(db.String(100))
    signa = db.Column(db.String(50))
    subtotal = db.Column(db.Float)

    item = db.relationship('ItemFarmasi')


class Racikan(db.Model):
    __tablename__ = 'racikan'
    id = db.Column(db.Integer, primary_key=True)
    resep_id = db.Column(db.Integer, db.ForeignKey('resep.id'))
    nama_racikan = db.Column(db.String(100))
    bentuk = db.Column(db.String(30))                   # puyer, kapsul, salep, cream
    qty_hasil = db.Column(db.Integer)
    aturan_pakai = db.Column(db.String(200))
    signa = db.Column(db.String(50))
    biaya_racik = db.Column(db.Float, default=0)

    komponen = db.relationship('RacikanKomponen', backref='racikan', lazy=True, cascade='all,delete')
    resep_items = db.relationship('ResepItem', backref='racikan', lazy=True)


class RacikanKomponen(db.Model):
    __tablename__ = 'racikan_komponen'
    id = db.Column(db.Integer, primary_key=True)
    racikan_id = db.Column(db.Integer, db.ForeignKey('racikan.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item_farmasi.id'))
    qty_dibutuhkan = db.Column(db.Float)
    satuan = db.Column(db.String(20))

    item = db.relationship('ItemFarmasi')


# ─── Stok & Distribusi ───────────────────────────────────

class Stok(db.Model):
    __tablename__ = 'stok'
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit_pelayanan.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item_farmasi.id'))
    batch = db.Column(db.String(50))
    ed = db.Column(db.Date)
    qty = db.Column(db.Float, default=0)
    harga_beli = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now)

    mutasi = db.relationship('MutasiStok', backref='stok_ref', lazy=True)


class MutasiStok(db.Model):
    __tablename__ = 'mutasi_stok'
    id = db.Column(db.Integer, primary_key=True)
    stok_id = db.Column(db.Integer, db.ForeignKey('stok.id'))
    tipe = db.Column(db.String(20))                     # masuk, keluar, distribusi, opname, expired
    referensi_id = db.Column(db.Integer)
    qty = db.Column(db.Float)                           # +masuk, -keluar
    sisa_stok = db.Column(db.Float)
    keterangan = db.Column(db.Text)
    user = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)


class Distribusi(db.Model):
    __tablename__ = 'distribusi'
    id = db.Column(db.Integer, primary_key=True)
    dari_unit_id = db.Column(db.Integer, db.ForeignKey('unit_pelayanan.id'))
    ke_unit_id = db.Column(db.Integer, db.ForeignKey('unit_pelayanan.id'))
    tanggal = db.Column(db.Date, default=date.today)
    no_distribusi = db.Column(db.String(30))
    keterangan = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    items = db.relationship('DistribusiItem', backref='distribusi', lazy=True, cascade='all,delete')
    dari_unit = db.relationship('UnitPelayanan', foreign_keys=[dari_unit_id])
    ke_unit = db.relationship('UnitPelayanan', foreign_keys=[ke_unit_id])


class DistribusiItem(db.Model):
    __tablename__ = 'distribusi_item'
    id = db.Column(db.Integer, primary_key=True)
    distribusi_id = db.Column(db.Integer, db.ForeignKey('distribusi.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item_farmasi.id'))
    qty = db.Column(db.Float)
    batch = db.Column(db.String(50))
    ed = db.Column(db.Date)

    item = db.relationship('ItemFarmasi')


# ─── Laporan Pustu ──────────────────────────────────────

class LaporanPustu(db.Model):
    __tablename__ = 'laporan_pustu'
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit_pelayanan.id'))
    tanggal_lapor = db.Column(db.Date, default=date.today)
    periode_bulan = db.Column(db.Integer)
    periode_tahun = db.Column(db.Integer)
    status = db.Column(db.String(20), default='draft')
    catatan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    items = db.relationship('LaporanPustuItem', backref='laporan', lazy=True, cascade='all,delete')
    unit = db.relationship('UnitPelayanan')


class LaporanPustuItem(db.Model):
    __tablename__ = 'laporan_pustu_item'
    id = db.Column(db.Integer, primary_key=True)
    laporan_id = db.Column(db.Integer, db.ForeignKey('laporan_pustu.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item_farmasi.id'))
    stok_awal = db.Column(db.Float)
    penerimaan = db.Column(db.Float)
    pemakaian = db.Column(db.Float)
    sisa = db.Column(db.Float)
    permintaan = db.Column(db.Float)

    item = db.relationship('ItemFarmasi')
