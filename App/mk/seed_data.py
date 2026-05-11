"""Seed data for Farmasi Puskesmas"""
from datetime import date
from models import db, Desa, KategoriItem, ItemFarmasi, UnitPelayanan, Dokter, Pasien

def seed_all():
    if Desa.query.first():
        return  # already seeded

    print("Seeding data...")

    # ── Desa ──────────────────────────────────────
    desa_names = [
        'Lonrong', 'Bijawang', 'Seppang', 'Padangloang', 'Salemba',
        'Dannuang', 'Manjalling', 'Garanta', 'Balong', 'Manyampa',
        'Balleanging', 'Tamatto', 'Paccarammengang'
    ]
    for n in desa_names:
        db.session.add(Desa(nama=n))
    db.session.commit()

    # ── Unit Pelayanan ────────────────────────────
    puskesmas = UnitPelayanan(
        nama='Puskesmas Ujung Loe', tipe='puskesmas',
        alamat='Jl. Poros Ujung Loe No. 1', desa_id=5,  # Salemba
        rawat_inap=True
    )
    db.session.add(puskesmas)
    db.session.commit()

    for d in desa_names[:4]:
        db.session.add(UnitPelayanan(
            nama=f'Pustu {d}', tipe='pustu',
            desa_id=Desa.query.filter_by(nama=d).first().id,
            induk_id=puskesmas.id
        ))

    # ── Dokter ────────────────────────────────────
    db.session.add(Dokter(nama='dr. Andi Nurhidayah', sip='123/SIP/BLK/2024', jenis='dokter', unit_id=puskesmas.id))
    db.session.add(Dokter(nama='dr. Muhammad Syukur', sip='124/SIP/BLK/2024', jenis='dokter', unit_id=puskesmas.id))
    db.session.add(Dokter(nama='Hasni, S.Farm, Apt', sip='125/SIPA/BLK/2024', jenis='apoteker', unit_id=puskesmas.id))
    db.session.add(Dokter(nama='Sitti Rahma, S.Keb', sip='126/SIB/BLK/2024', jenis='bidan', unit_id=puskesmas.id))
    db.session.add(Dokter(nama='Ahmad, S.Kep', sip='127/SIK/BLK/2024', jenis='perawat', unit_id=puskesmas.id))

    # ── Kategori ──────────────────────────────────
    kat_obat = KategoriItem(nama='Analgesik & Antipiretik', tipe='obat')
    db.session.add(kat_obat)
    kat_antibiotik = KategoriItem(nama='Antibiotik', tipe='obat')
    db.session.add(kat_antibiotik)
    kat_ht = KategoriItem(nama='Antihipertensi & Jantung', tipe='obat')
    db.session.add(kat_ht)
    kat_dm = KategoriItem(nama='Antidiabetes', tipe='obat')
    db.session.add(kat_dm)
    kat_cerna = KategoriItem(nama='Saluran Cerna', tipe='obat')
    db.session.add(kat_cerna)
    kat_nafas = KategoriItem(nama='Saluran Nafas', tipe='obat')
    db.session.add(kat_nafas)
    kat_kulit = KategoriItem(nama='Kulit & Salep', tipe='obat')
    db.session.add(kat_kulit)
    kat_vit = KategoriItem(nama='Vitamin & Mineral', tipe='obat')
    db.session.add(kat_vit)
    kat_nark = KategoriItem(nama='Narkotik & Psikotropik', tipe='obat')
    db.session.add(kat_nark)
    kat_bhp = KategoriItem(nama='BHP Infus & Suntik', tipe='bhp')
    db.session.add(kat_bhp)
    kat_bhp2 = KategoriItem(nama='BHP Luka & Jahit', tipe='bhp')
    db.session.add(kat_bhp2)
    kat_bhp3 = KategoriItem(nama='BHP APD & Lab', tipe='bhp')
    db.session.add(kat_bhp3)
    db.session.commit()

    # ── Obat ──────────────────────────────────────
    obats = [
        # (kategori_nama, nama_generik, bentuk, kekuatan, satuan, gol, racikan)
        ('Analgesik & Antipiretik', 'Parasetamol', 'Tab', '500 mg', 'tab', 'bebas'),
        ('Analgesik & Antipiretik', 'Parasetamol', 'Sir', '120 mg/5 mL', 'btl', 'bebas'),
        ('Analgesik & Antipiretik', 'Parasetamol', 'Drops', '100 mg/mL', 'btl', 'bebas'),
        ('Analgesik & Antipiretik', 'Asam Mefenamat', 'Kaps', '500 mg', 'kaps', 'bebas'),
        ('Analgesik & Antipiretik', 'Ibuprofen', 'Tab', '400 mg', 'tab', 'bebas'),
        ('Analgesik & Antipiretik', 'Natrium Diklofenak', 'Tab', '50 mg', 'tab', 'bebas'),
        ('Analgesik & Antipiretik', 'Alopurinol', 'Tab', '100 mg', 'tab', 'bebas'),
        ('Antibiotik', 'Amoksisilin', 'Kaps', '500 mg', 'kaps', 'terbatas', True),
        ('Antibiotik', 'Amoksisilin', 'Sir', '125 mg/5 mL', 'btl', 'terbatas', True),
        ('Antibiotik', 'Kotrimoksazol', 'Tab', '480 mg', 'tab', 'terbatas', True),
        ('Antibiotik', 'Metronidazol', 'Tab', '500 mg', 'tab', 'terbatas', True),
        ('Antibiotik', 'Sefadroksil', 'Kaps', '500 mg', 'kaps', 'terbatas', True),
        ('Antibiotik', 'Tetrasiklin', 'Kaps', '250 mg', 'kaps', 'terbatas', True),
        ('Antibiotik', 'Kloramfenikol', 'Kaps', '250 mg', 'kaps', 'terbatas', True),
        ('Antihipertensi & Jantung', 'Kaptopril', 'Tab', '25 mg', 'tab', 'terbatas'),
        ('Antihipertensi & Jantung', 'Nifedipin', 'Tab', '10 mg', 'tab', 'terbatas'),
        ('Antihipertensi & Jantung', 'Propranolol', 'Tab', '40 mg', 'tab', 'terbatas'),
        ('Antihipertensi & Jantung', 'Hidroklorotiazid', 'Tab', '25 mg', 'tab', 'terbatas'),
        ('Antihipertensi & Jantung', 'Digoksin', 'Tab', '0,25 mg', 'tab', 'terbatas'),
        ('Antihipertensi & Jantung', 'Simvastatin', 'Tab', '20 mg', 'tab', 'terbatas'),
        ('Antihipertensi & Jantung', 'Klopidogrel', 'Tab', '75 mg', 'tab', 'terbatas'),
        ('Antihipertensi & Jantung', 'Asam Asetilsalisilat', 'Tab', '80 mg', 'tab', 'bebas'),
        ('Antidiabetes', 'Metformin', 'Tab', '500 mg', 'tab', 'terbatas'),
        ('Antidiabetes', 'Glibenklamid', 'Tab', '5 mg', 'tab', 'terbatas'),
        ('Saluran Cerna', 'Antasida', 'Tab', '', 'tab', 'bebas'),
        ('Saluran Cerna', 'Omeprazol', 'Kaps', '20 mg', 'kaps', 'terbatas'),
        ('Saluran Cerna', 'Ranitidin', 'Tab', '150 mg', 'tab', 'terbatas'),
        ('Saluran Cerna', 'Bisakodil', 'Tab', '5 mg', 'tab', 'bebas'),
        ('Saluran Cerna', 'Loperamid', 'Kaps', '2 mg', 'kaps', 'bebas'),
        ('Saluran Na fas', 'Salbutamol', 'Tab', '4 mg', 'tab', 'terbatas'),
        ('Saluran Na fas', 'Salbutamol', 'Sir', '2 mg/5 mL', 'btl', 'terbatas'),
        ('Saluran Na fas', 'Deksametason', 'Tab', '0,5 mg', 'tab', 'terbatas', True),
        ('Saluran Na fas', 'Prednison', 'Tab', '5 mg', 'tab', 'terbatas'),
        ('Saluran Na fas', 'CTM (Klorfeniramin Maleat)', 'Tab', '4 mg', 'tab', 'bebas', True),
        ('Kulit & Salep', 'Mikonazol', 'Cream', '2%', 'tube', 'bebas'),
        ('Kulit & Salep', 'Betametason', 'Cream', '0,1%', 'tube', 'terbatas'),
        ('Kulit & Salep', 'Gentamisin Sulfat', 'Cream', '0,1%', 'tube', 'terbatas'),
        ('Kulit & Salep', 'Asiklovir', 'Cream', '5%', 'tube', 'terbatas'),
        ('Kulit & Salep', 'Asiklovir', 'Tab', '400 mg', 'tab', 'terbatas'),
        ('Vitamin & Mineral', 'Vitamin C', 'Tab', '250 mg', 'tab', 'bebas'),
        ('Vitamin & Mineral', 'Vitamin B6', 'Tab', '10 mg', 'tab', 'bebas'),
        ('Vitamin & Mineral', 'Vitamin B Kompleks', 'Tab', '', 'tab', 'bebas'),
        ('Vitamin & Mineral', 'Zat Besi (Fe)', 'Tab', '60 mg', 'tab', 'bebas'),
        ('Vitamin & Mineral', 'Asam Folat', 'Tab', '1 mg', 'tab', 'bebas'),
        ('Vitamin & Mineral', 'Vitamin D', 'Tab', '400 IU', 'tab', 'bebas'),
        ('Vitamin & Mineral', 'Zink', 'Tab', '20 mg', 'tab', 'bebas'),
        ('Vitamin & Mineral', 'Kalsium Laktat', 'Tab', '500 mg', 'tab', 'bebas'),
        ('Narkotik & Psikotropik', 'Diazepam', 'Tab', '5 mg', 'tab', 'psikotropik'),
        ('Narkotik & Psikotropik', 'Kodein', 'Tab', '10 mg', 'tab', 'narkotik'),
        ('Narkotik & Psikotropik', 'Fenobarbital', 'Tab', '30 mg', 'tab', 'psikotropik'),
        # BHP
        ('BHP Infus & Suntik', 'Infus Set (Makro)', '', '', 'set', 'bebas'),
        ('BHP Infus & Suntik', 'Infus Set (Mikro)', '', '', 'set', 'bebas'),
        ('BHP Infus & Suntik', 'Abocath No 22', '', '', 'pcs', 'bebas'),
        ('BHP Infus & Suntik', 'Abocath No 24', '', '', 'pcs', 'bebas'),
        ('BHP Infus & Suntik', 'Spuit 1 mL (Insulin)', '', '', 'pcs', 'bebas'),
        ('BHP Infus & Suntik', 'Spuit 3 mL', '', '', 'pcs', 'bebas'),
        ('BHP Infus & Suntik', 'Spuit 5 mL', '', '', 'pcs', 'bebas'),
        ('BHP Infus & Suntik', 'Spuit 10 mL', '', '', 'pcs', 'bebas'),
        ('BHP Infus & Suntik', 'NaCl 0,9% (Kolf)', '', '', 'btl', 'bebas'),
        ('BHP Infus & Suntik', 'Cairan RL (Kolf)', '', '', 'btl', 'bebas'),
        ('BHP Luka & Jahit', 'Kasa Steril', '', '', 'bungkus', 'bebas'),
        ('BHP Luka & Jahit', 'Kapas', '', '', 'bungkus', 'bebas'),
        ('BHP Luka & Jahit', 'Plester (Hipafix)', '', '', 'rol', 'bebas'),
        ('BHP Luka & Jahit', 'Verban / Perban', '', '', 'rol', 'bebas'),
        ('BHP Luka & Jahit', 'Benang Jahit Silk 3/0', '', '', 'pcs', 'bebas'),
        ('BHP Luka & Jahit', 'Mata Pisau Scalpel No 11', '', '', 'pcs', 'bebas'),
        ('BHP Luka & Jahit', 'Povidone Iodine 10%', '', '', 'btl', 'bebas'),
        ('BHP Luka & Jahit', 'Alkohol 70%', '', '', 'btl', 'bebas'),
        ('BHP APD & Lab', 'Handscoon (M) Non Steril', '', '', 'box', 'bebas'),
        ('BHP APD & Lab', 'Handscoon (L) Non Steril', '', '', 'box', 'bebas'),
        ('BHP APD & Lab', 'Masker Bedah 3 ply', '', '', 'box', 'bebas'),
        ('BHP APD & Lab', 'Strip Glukosa Darah', '', '', 'box', 'bebas'),
        ('BHP APD & Lab', 'Lancet', '', '', 'pcs', 'bebas'),
        ('BHP APD & Lab', 'Alcohol Swab', '', '', 'box', 'bebas'),
        ('BHP APD & Lab', 'Jelly USG', '', '', 'tube', 'bebas'),
        ('BHP APD & Lab', 'Underpad', '', '', 'pcs', 'bebas'),
        ('BHP APD & Lab', 'Selang Oksigen (Nasal)', '', '', 'pcs', 'bebas'),
    ]

    for o in obats:
        kat = KategoriItem.query.filter_by(nama=o[0]).first()
        if not kat: continue
        item = ItemFarmasi(
            kategori_id=kat.id,
            nama_generik=o[1], bentuk=o[2], kekuatan=o[3],
            satuan=o[4], golongan=o[5],
            tipe='bhp' if o[0].startswith('BHP') else 'obat',
            racikan=len(o) > 6 and o[6],
            fornas='BHP' not in o[0]
        )
        db.session.add(item)
    db.session.commit()

    # ── Pasien ─────────────────────────────────────
    pasien_data = [
        ('7302110101940001', '0001234567890', 'Andi Sitti Nur Rahmi', 'P', 'Ujung Loe', '1994-01-01', 'Dannuang'),
        ('7302110101950002', '0002234567891', 'Muhammad Basri S.', 'L', 'Ujung Loe', '1995-02-15', 'Salemba'),
        ('7302110101960003', '0003234567892', 'Hasni binti Kahar', 'P', 'Bantaeng', '1996-03-20', 'Lonrong'),
        ('7302110101970004', '0004234567893', 'Abdul Rasyid Dg. Ngirate', 'L', 'Bulukumba', '1997-04-10', 'Bijawang'),
        ('7302110101980005', '0005234567894', 'St. Halimah Dg. Nganjing', 'P', 'Ujung Loe', '1998-05-05', 'Seppang'),
        ('7302110101990006', '0006234567895', 'Jamaluddin Dg. Nompo', 'L', 'Bulukumba', '1999-06-15', 'Manjalling'),
        ('7302110102000007', '0007234567896', 'Hj. Fatimah Dg. Nisau', 'P', 'Bantaeng', '2000-07-25', 'Padangloang'),
        ('7302110102010008', '0008234567897', 'Hermansyah Dg. Lira', 'L', 'Ujung Loe', '2001-08-30', 'Garanta'),
        ('7302110102020009', '0009234567898', 'Nurhidayah binti Ali', 'P', 'Bulukumba', '2002-09-12', 'Manyampa'),
        ('7302110102030010', '0010234567899', 'Samsu Alam Dg. Nibung', 'L', 'Ujung Loe', '2003-10-18', 'Balong'),
        ('7302110102040011', '0011234567801', 'Rahmatia Dg. Ngana', 'P', 'Bulukumba', '2004-11-22', 'Balleanging'),
        ('7302110102050012', '0012234567802', 'M. Tahir Dg. Situru', 'L', 'Ujung Loe', '2005-12-01', 'Tamatto'),
        ('7302110102060013', '0013234567803', 'Kartini Dg. Tassu', 'P', 'Bantaeng', '2006-01-14', 'Paccarammengang'),
        ('7302110102070014', '0014234567804', 'Saiful Dg. Tutu', 'L', 'Bulukumba', '2007-02-10', 'Dannuang'),
    ]

    for p in pasien_data:
        desa = Desa.query.filter_by(nama=p[5]).first()
        db.session.add(Pasien(
            nik=p[0], no_bpjs=p[1], nama=p[2], jenis_kelamin=p[3],
            tempat_lahir=p[4], tanggal_lahir=date.fromisoformat(p[5]) if isinstance(p[5], str) else date(2000,1,1),
            alamat=f'Dusun Bonto, {p[5]}', desa_id=desa.id if desa else None
        ))
    db.session.commit()
    print(f"Seed OK: {Desa.query.count()} desa, {ItemFarmasi.query.count()} items, {Pasien.query.count()} pasien")
