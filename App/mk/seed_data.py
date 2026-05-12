from models import db, Obat, Kategori, Satuan, Supplier, Pelanggan, User


def seed_all():
    if Kategori.query.first():
        return

    # ── Kategori ──
    kat_list = [
        'Antibiotik', 'Analgesik', 'Antipiretik', 'Vitamin & Suplemen',
        'Antihistamin', 'Antasida', 'Antihipertensi', 'Antidiabetes',
        'Kardiovaskular', 'Saluran Nafas', 'Saluran Cerna', 'Kulit & Topikal',
        'Mata & Telinga', 'Saraf & Psikotropika', 'Narkotika', 'Herbal',
        'Alat Kesehatan', 'Lain-lain'
    ]
    for k in kat_list:
        db.session.add(Kategori(nama_kategori=k))

    # ── Satuan ──
    sat_list = [
        ('Tablet', 'tbl'), ('Kapsul', 'kps'), ('Ampul', 'amp'),
        ('Botol', 'btl'), ('Tube', 'tube'), ('Strip', 'str'),
        ('Vial', 'vial'), ('Lembar', 'lbr'), ('Pcs', 'pcs'),
        ('Box', 'box'), ('Sachet', 'sct'), ('ml', 'ml'), ('Gram', 'gr'),
    ]
    for n, s in sat_list:
        db.session.add(Satuan(nama_satuan=n, singkatan=s))

    # ── Supplier ──
    db.session.add(Supplier(nama='PT Indofarma (Persero) Tbk', kota='Jakarta',
                            telepon='021-123456', syarat_bayar='Tempo 30 hari'))
    db.session.add(Supplier(nama='PT Kimia Farma Tbk', kota='Bandung',
                            telepon='022-789012', syarat_bayar='Tempo 14 hari'))
    db.session.add(Supplier(nama='PT Kalbe Farma Tbk', kota='Jakarta',
                            telepon='021-345678', syarat_bayar='Tunai'))
    db.session.add(Supplier(nama='K24 Cabang Bulukumba', kota='Bulukumba',
                            telepon='0413-12345', syarat_bayar='Tunai'))

    # ── User ──
    users = [
        ('Admin Utama', 'admin', 'admin123', 'super_admin', ''),
        ('Apoteker Ujang', 'apoteker', 'apoteker123', 'apoteker', 'SIPA.2026.001'),
        ('Kasir Dewi', 'kasir', 'kasir123', 'kasir', ''),
        ('Gudang Budi', 'gudang', 'gudang123', 'gudang', ''),
    ]
    for nama, username, pw, role, sipa in users:
        u = User(nama=nama, username=username, role=role, no_sipa=sipa)
        u.set_password(pw)
        db.session.add(u)

    # ── Obat sample ──
    db.session.add(Obat(kode_obat='OBT001', nama_generik='Paracetamol',
                        nama_dagang='Paracetamol 500mg', id_kategori=2,
                        id_satuan=1, golongan='Bebas', harga_beli=5000,
                        harga_jual_eceran=8000, harga_jual_resep=7500,
                        stok_minimum=50))
    db.session.add(Obat(kode_obat='OBT002', nama_generik='Amoksisilin',
                        nama_dagang='Amoksisilin 500mg', id_kategori=1,
                        id_satuan=1, golongan='Keras', harga_beli=8000,
                        harga_jual_eceran=12000, harga_jual_resep=11000,
                        stok_minimum=30))
    db.session.add(Obat(kode_obat='OBT003', nama_generik='Vitamin C',
                        nama_dagang='Vit-C 50mg', id_kategori=4,
                        id_satuan=1, golongan='Bebas', harga_beli=2000,
                        harga_jual_eceran=5000, harga_jual_resep=4500,
                        stok_minimum=100))
    db.session.add(Obat(kode_obat='OBT004', nama_generik='Antasida DOEN',
                        nama_dagang='Antasida Tablet', id_kategori=6,
                        id_satuan=1, golongan='Bebas', harga_beli=3000,
                        harga_jual_eceran=6000, harga_jual_resep=5500,
                        stok_minimum=50))
    db.session.add(Obat(kode_obat='OBT005', nama_generik='Diazepam',
                        nama_dagang='Diazepam 5mg', id_kategori=14,
                        id_satuan=1, golongan='Psikotropika', harga_beli=15000,
                        harga_jual_eceran=25000, harga_jual_resep=22000,
                        stok_minimum=10))

    # ── Pelanggan sample ──
    db.session.add(Pelanggan(kode_member='MBR001', nama='Siti Nurhaliza',
                             telepon='081234567890', alamat='Jl. Merdeka No.1'))

    db.session.commit()
    print("✅ Seed data berhasil dimuat")
