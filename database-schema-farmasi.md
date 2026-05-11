# Database Schema — Aplikasi Farmasi Puskesmas

**RDBMS:** SQLite (MVP) → PostgreSQL (scale)
**ORM:** Flask-SQLAlchemy (karena backend Flask)

---

## 🔷 Tabel-Tabel

### 1. `unit_pelayanan` — Puskesmas & Unit Bawah
```sql
id         INT PK AUTO
nama       VARCHAR(100)       -- "Puskesmas Ujung Loe", "Pustu Lonrong"
tipe       VARCHAR(20)        -- 'puskesmas', 'pustu', 'polindes', 'poskesdes'
alamat     TEXT
desa_id    INT FK -> desa.id
induk_id   INT FK -> unit_pelayanan.id NULL  -- null kalo puskesmas induk
rawat_inap BOOLEAN DEFAULT 0  -- punya rawat inap atau tidak
aktif      BOOLEAN DEFAULT 1
```

### 2. `desa` — Referensi Desa (Ujung Loe)
```sql
id         INT PK AUTO
nama       VARCHAR(100)
kecamatan  VARCHAR(100) DEFAULT 'Ujung Loe'
kabupaten  VARCHAR(100) DEFAULT 'Bulukumba'
provinsi   VARCHAR(100) DEFAULT 'Sulawesi Selatan'
```

### 3. `kategori_item` — Kategori Obat & BHP
```sql
id         INT PK AUTO
nama       VARCHAR(100)       -- 'Analgesik', 'Antibiotik', 'BHP Infus', dll
tipe       VARCHAR(10)        -- 'obat' atau 'bhp'
```

### 4. `item_farmasi` — Master Obat & BHP (SEED DATA)
```sql
id                  INT PK AUTO
kategori_id         INT FK -> kategori_item.id
kode                VARCHAR(50) NULL     -- kode e-katalog / KFA (untuk barcode nanti)
nama_generik        VARCHAR(200)         -- 'Amoksisilin'
nama_dagang         VARCHAR(200) NULL    -- 'Amoxil', dll (bisa null kalo OGB)
bentuk              VARCHAR(50)          -- 'Tab', 'Kaps', 'Sir', 'Inj', 'Cream', dll
kekuatan            VARCHAR(50)          -- '500 mg', '250 mg/5 mL', NULL (BHP)
satuan              VARCHAR(20)          -- 'tab', 'btl', 'box', 'set', 'pcs'
tipe                VARCHAR(10)          -- 'obat' / 'bhp'
golongan            VARCHAR(20)          -- 'bebas', 'terbatas', 'narkotik', 'psikotropik'
fornas              BOOLEAN DEFAULT 1    -- apakah masuk FORNAS
racikan             BOOLEAN DEFAULT 0    -- bisa diracik? (obat aja)
harga_acuan         DECIMAL(12,2) NULL   -- harga eceran acuan
aktif               BOOLEAN DEFAULT 1
batas_min_stok      INT DEFAULT 10       -- untuk notifikasi
```

### 5. `pasien` — Data Pasien
```sql
id                  INT PK AUTO
nik                 VARCHAR(16)          -- NIK 16 digit
no_bpjs             VARCHAR(20) NULL     -- No. Kartu BPJS
nama                VARCHAR(200)
jenis_kelamin       VARCHAR(1)           -- 'L' / 'P'
tempat_lahir        VARCHAR(100)
tanggal_lahir       DATE
alamat              TEXT
desa_id             INT FK -> desa.id
telepon             VARCHAR(20) NULL
pekerjaan           VARCHAR(100) NULL
created_at          DATETIME
updated_at          DATETIME
```

### 6. `dokter` — Tenaga Kesehatan
```sql
id              INT PK AUTO
nama            VARCHAR(200)
sip             VARCHAR(50) NULL    -- No. SIP
jenis           VARCHAR(30)         -- 'dokter', 'bidan', 'perawat', 'apoteker'
unit_id         INT FK -> unit_pelayanan.id
aktif           BOOLEAN DEFAULT 1
```

### 7. `resep` — Resep / Pelayanan Farmasi (HEADER)
```sql
id                  INT PK AUTO
no_resep            VARCHAR(30) UNIQUE  -- auto-generated (R-20260511-001)
tanggal             DATE
jenis_pelayanan     VARCHAR(10) DEFAULT 'RAWAT_JALAN'  -- 'RAWAT_JALAN', 'RAWAT_INAP'
no_rm               VARCHAR(20) NULL     -- No. Rekam Medis (kalo rawat inap)
no_kamar            VARCHAR(20) NULL     -- Kamar rawat inap
pasien_id           INT FK -> pasien.id
dokter_id           INT FK -> dokter.id
unit_id             INT FK -> unit_pelayanan.id
keluhan             TEXT NULL            -- diagnosa
jaminan             VARCHAR(20)          -- 'BPJS', 'JAMKESDA', 'UMUM', 'LAIN'
no_sep              VARCHAR(30) NULL     -- Nomor SEP BPJS
status              VARCHAR(20) DEFAULT 'baru'  -- 'baru','siap','diambil','ditunda','diberikan'
created_by          VARCHAR(100)
created_at          DATETIME
updated_at          DATETIME
```

### 8. `resep_item` — Detail Obat per Resep
```sql
id              INT PK AUTO
resep_id        INT FK -> resep.id
item_id         INT FK -> item_farmasi.id   -- obat yang dipilih
racikan_id      INT FK -> racikan.id NULL   -- kalo termasuk racikan
qty             DECIMAL(10,2)               -- jumlah
aturan          VARCHAR(100)                -- '3x1', '2x1', '1x1'
signa           VARCHAR(50) NULL            -- 'pagi/siang/malam'
subtotal        DECIMAL(12,2) NULL
```

### 9. `racikan` — Resep Racikan (HEADER Racikan)
```sql
id              INT PK AUTO
resep_id        INT FK -> resep.id
nama_racikan    VARCHAR(100)        -- 'Puyer 1', 'Salep Racik'
bentuk          VARCHAR(30)         -- 'puyer', 'kapsul', 'salep', 'cream', 'lotion'
qty_hasil       INT                 -- jumlah hasil racikan
aturan_pakai    VARCHAR(200)
signa           VARCHAR(50)
biaya_racik     DECIMAL(10,2) DEFAULT 0
```

### 10. `racikan_komponen` — Bahan Racikan
```sql
id              INT PK AUTO
racikan_id      INT FK -> racikan.id
item_id         INT FK -> item_farmasi.id
qty_dibutuhkan  DECIMAL(10,2)
satuan          VARCHAR(20)         -- 'mg', 'g', 'ml', 'tab'
```

### 11. `stok` — Stok per Unit Pelayanan
```sql
id              INT PK AUTO
unit_id         INT FK -> unit_pelayanan.id
item_id         INT FK -> item_farmasi.id
batch           VARCHAR(50) NULL     -- no batch
ed              DATE NULL            -- tanggal kadaluarsa
qty             DECIMAL(10,2)        -- jumlah stok saat ini
harga_beli      DECIMAL(12,2) NULL
created_at      DATETIME
updated_at      DATETIME
```

### 12. `mutasi_stok` — Riwayat Mutasi Stok
```sql
id              INT PK AUTO
stok_id         INT FK -> stok.id
tipe            VARCHAR(20)      -- 'masuk', 'keluar', 'distribusi', 'opname', 'expired'
referensi_id    INT NULL         -- ID dari transaksi terkait (resep, distribusi, dll)
qty             DECIMAL(10,2)    -- + = masuk, - = keluar
sisa_stok       DECIMAL(10,2)    -- sisa setelah mutasi
keterangan      TEXT NULL
user            VARCHAR(100)
created_at      DATETIME
```

### 13. `distribusi` — Distribusi ke Unit Bawah (Header)
```sql
id              INT PK AUTO
dari_unit_id    INT FK -> unit_pelayanan.id    -- puskesmas
ke_unit_id      INT FK -> unit_pelayanan.id    -- pustu/polindes
tanggal         DATE
no_distribusi   VARCHAR(30)
keterangan      TEXT NULL
created_by      VARCHAR(100)
created_at      DATETIME
```

### 14. `distribusi_item` — Detail Distribusi
```sql
id              INT PK AUTO
distribusi_id   INT FK -> distribusi.id
item_id         INT FK -> item_farmasi.id
qty             DECIMAL(10,2)
batch           VARCHAR(50) NULL
ed              DATE NULL
```

### 15. `laporan_pustu` — Laporan Pemakaian dari Unit Bawah
```sql
id              INT PK AUTO
unit_id         INT FK -> unit_pelayanan.id   -- pustu yg lapor
tanggal_lapor   DATE
periode_bulan   INT              -- bulan laporan
periode_tahun   INT              -- tahun laporan
status          VARCHAR(20) DEFAULT 'draft'   -- 'draft', 'dikirim', 'diterima'
catatan         TEXT NULL
created_at      DATETIME
```

### 16. `laporan_pustu_item` — Detail Laporan
```sql
id              INT PK AUTO
laporan_id      INT FK -> laporan_pustu.id
item_id         INT FK -> item_farmasi.id
stok_awal       DECIMAL(10,2)
penerimaan      DECIMAL(10,2)
pemakaian       DECIMAL(10,2)
sisa            DECIMAL(10,2)
permintaan      DECIMAL(10,2) NULL   -- permintaan untuk bulan depan
```

---

## 🔷 Relasi Antar Tabel (Gambaran)

```
unit_pelayanan ──┬── dokter
                 ├── stok ── item_farmasi
                 ├── distribusi ─┬─ distribusi_item ── item_farmasi
                 └── laporan_pustu ─┬─ laporan_pustu_item
                
pasien ──┬── resep ─┬── resep_item ── item_farmasi
         │          └── racikan ──┬─ racikan_komponen ── item_farmasi
         │                        └─ resep_item (link back)
         
item_farmasi ──┬── kategori_item
               ├── stok
               ├── mutasi_stok
               ├── resep_item
               └── distribusi_item

desa ──┬── pasien
       └── unit_pelayanan
```

---

## 🔷 Ringkasan

| # | Tabel | Fungsi |
|---|-------|--------|
| 1 | `unit_pelayanan` | Puskesmas + Pustu/Polindes/Poskesdes |
| 2 | `desa` | Referensi wilayah |
| 3 | `kategori_item` | Kategori farmasi |
| 4 | `item_farmasi` | **Master obat + BHP** (seed data) |
| 5 | `pasien` | Data pasien |
| 6 | `dokter` | Tenaga kesehatan |
| 7 | `resep` | Header pelayanan resep |
| 8 | `resep_item` | Detail obat per resep |
| 9 | `racikan` | Header racikan |
| 10 | `racikan_komponen` | Bahan-bahan racikan |
| 11 | `stok` | Stok per unit + batch + ED |
| 12 | `mutasi_stok` | Riwayat semua mutasi (audit trail) |
| 13 | `distribusi` | Distribusi ke unit bawah |
| 14 | `distribusi_item` | Detail distribusi |
| 15 | `laporan_pustu` | Laporan periodik dari unit |
| 16 | `laporan_pustu_item` | Detail laporan |

---

**Total: 16 tabel.** Cukup komprehensif tapi gak berlebihan. Kalo ada yang perlu ditambah/dikurang, bilang aja 😎
