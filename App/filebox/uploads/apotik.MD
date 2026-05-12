markdown
Copy
# 📋 Spesifikasi Aplikasi Apotek Mandiri
**Versi:** 1.0.0  
**Tanggal:** 2025  
**Status:** Draft untuk Evaluasi

---

## 1. OVERVIEW PROYEK

### 1.1 Deskripsi
Aplikasi manajemen apotek mandiri berbasis web/desktop yang mencakup seluruh proses operasional apotek — dari pengadaan obat, pelayanan resep, transaksi kasir, hingga laporan keuangan dan stok.

### 1.2 Tujuan
- Mempercepat dan mengakuratkan proses pelayanan pasien/pelanggan
- Mengontrol stok obat secara real-time termasuk expired date
- Menghasilkan laporan bisnis yang akurat untuk pengambilan keputusan
- Memenuhi regulasi pencatatan obat keras, narkotika, dan psikotropika

### 1.3 Scope
| Termasuk | Tidak Termasuk (fase ini) |
|---|---|
| Manajemen stok & obat | Integrasi BPJS |
| Pembelian & pengadaan | Multi-cabang |
| Kasir & POS | E-commerce / online store |
| Laporan keuangan | Integrasi akuntansi eksternal |
| Manajemen user & role | Mobile app |
| Pelayanan resep | |
| Loyalty pelanggan | |

---

## 2. MODUL & FITUR

### 2.1 Modul Master Data

**M01 - Master Obat**
- CRUD data obat (nama generik, nama dagang/branded)
- Kategori obat (antibiotik, vitamin, analgesik, dll.)
- Golongan obat: Bebas / Bebas Terbatas / Keras / Narkotika / Psikotropika
- Satuan (tablet, kapsul, botol, ampul, dll.)
- Harga beli & harga jual (bisa multi harga jual: eceran, resep, grosir)
- Stok minimum (trigger alert)
- Gambar obat (opsional)
- Status aktif/nonaktif

**M02 - Master Supplier/Distributor**
- CRUD data supplier (nama, alamat, kontak, NPWP)
- PIC supplier
- Syarat pembayaran (COD, tempo 14/30 hari)
- Riwayat transaksi per supplier

**M03 - Master Pelanggan**
- CRUD data pelanggan (nama, kontak, alamat, tanggal lahir)
- Riwayat pembelian
- Poin loyalty
- Alergi obat (opsional, untuk keamanan)

**M04 - Master Pegawai**
- CRUD data pegawai (nama, SIPA/SIPTTK untuk apoteker)
- Role / jabatan
- Username & password
- Status aktif

**M05 - Master Kategori & Satuan**
- Kelola kategori obat
- Kelola satuan obat
- Kelola lokasi rak/penyimpanan (opsional)

---

### 2.2 Modul Pengadaan & Pembelian

**P01 - Purchase Order (PO)**
- Buat PO ke supplier
- Detail item: obat, jumlah, harga beli, diskon
- Status PO: Draft → Terkirim → Sebagian Diterima → Selesai → Dibatalkan
- Cetak PO (format PDF)

**P02 - Penerimaan Barang**
- Input penerimaan berdasarkan PO (atau tanpa PO)
- Verifikasi item: jumlah aktual, batch number, expired date
- Alert jika expired date < 6 bulan dari sekarang
- Update stok otomatis setelah konfirmasi
- Simpan faktur supplier

**P03 - Retur Pembelian**
- Retur obat ke supplier (rusak, salah kirim, mendekati expired)
- Kurangi stok otomatis
- Cetak surat retur

**P04 - Hutang Supplier**
- Daftar hutang berdasarkan faktur
- Pembayaran hutang (tunai / transfer)
- Riwayat pembayaran
- Alert jatuh tempo

---

### 2.3 Modul Stok & Gudang

**S01 - Manajemen Stok**
- Tampilan stok real-time per obat
- Stok per batch (FEFO — First Expired First Out)
- Filter: hampir habis, hampir expired, kritis
- History mutasi stok (masuk/keluar/adjustment)

**S02 - Stok Opname**
- Buat sesi stok opname
- Input hitungan fisik
- Sistem tampilkan selisih (sistem vs fisik)
- Approval adjustment oleh admin/apoteker
- Laporan hasil opname

**S03 - Alert & Notifikasi**
- Notifikasi stok di bawah minimum
- Notifikasi obat expired dalam 1 bulan / 3 bulan
- Notifikasi hutang jatuh tempo

**S04 - Penyesuaian Stok Manual**
- Adjustment stok (dengan alasan wajib diisi)
- Log semua adjustment (audit trail)

---

### 2.4 Modul Pelayanan & Resep

**R01 - Input Resep**
- Input data resep (nama dokter, nama pasien, tanggal)
- Detail obat: nama, jumlah, aturan pakai, signa
- Validasi oleh apoteker (konfirmasi sebelum disiapkan)
- Status resep: Masuk → Diproses → Siap → Selesai

**R02 - Pelayanan OTC (Tanpa Resep)**
- Penjualan langsung tanpa resep
- Sistem tetap mencatat untuk obat bebas terbatas

**R03 - Etiket Obat**
- Generate & cetak etiket otomatis dari data resep
- Format: nama pasien, nama obat, aturan pakai, tanggal, nama apotek

**R04 - Riwayat Resep Pelanggan**
- Cari riwayat resep berdasarkan nama/kontak pelanggan
- Berguna untuk pembelian ulang (copy resep)

---

### 2.5 Modul Kasir / POS

**K01 - Transaksi Penjualan**
- Tambah item via search nama/barcode scan
- Quantity, harga jual, diskon per item
- Diskon global transaksi
- Pilih pelanggan (untuk loyalty poin)
- Terhubung ke resep (jika dari resep)
- Kalkulasi otomatis total, diskon, PPN (jika ada), kembalian

**K02 - Metode Pembayaran**
- Tunai
- Transfer bank
- QRIS / e-wallet
- Kombinasi (split payment)

**K03 - Cetak Struk**
- Thermal printer (58mm / 80mm)
- Struk berisi: nama apotek, alamat, no. SIPA, detail item, total, kasir, tanggal

**K04 - Void & Retur Penjualan**
- Void transaksi (hari yang sama, butuh otorisasi)
- Retur penjualan (beda hari, stok kembali)
- Log retur dengan alasan

**K05 - Shift Kasir**
- Buka shift (input saldo awal)
- Tutup shift (hitung total penjualan, saldo akhir, selisih)
- Laporan per shift

---

### 2.6 Modul Keuangan

**F01 - Laporan Penjualan**
- Penjualan harian / mingguan / bulanan / custom range
- Per kasir, per kategori obat, per metode bayar
- Grafik tren penjualan

**F02 - Laporan Laba Rugi Sederhana**
- Pendapatan vs HPP (Harga Pokok Penjualan)
- Gross profit per periode
- Per obat / kategori

**F03 - Laporan Hutang & Piutang**
- Rekap hutang ke supplier
- Status pembayaran

**F04 - Laporan Pengeluaran Operasional**
- Input pengeluaran manual (listrik, gaji, dll.)
- Ringkasan pengeluaran per periode

---

### 2.7 Modul Laporan Regulasi

**L01 - Laporan Narkotika & Psikotropika**
- Rekap pemakaian per bulan
- Format sesuai kebutuhan pelaporan SIPNAP BPOM
- Export Excel/PDF

**L02 - Laporan Stok**
- Kartu stok per obat
- Laporan expired
- Laporan slow moving (obat jarang terjual)

---

### 2.8 Modul Loyalty Pelanggan

**LY01 - Poin Reward**
- Akumulasi poin dari setiap transaksi (contoh: Rp10.000 = 1 poin)
- Penukaran poin saat transaksi
- Riwayat poin per pelanggan
- Konfigurasi nilai poin (fleksibel oleh admin)

**LY02 - Member Card**
- Cetak / generate kartu member (dengan QR/barcode)
- Scan member card saat transaksi

---

### 2.9 Modul User & Hak Akses

**U01 - Role Management**

| Role | Akses |
|---|---|
| Super Admin | Semua fitur + konfigurasi sistem |
| Apoteker | Semua fitur kecuali konfigurasi sistem |
| TTK | Pelayanan, kasir, stok (view) |
| Kasir | Kasir, pelayanan OTC |
| Gudang | Pengadaan, stok |
| Pemilik/Manajer | Semua laporan, view-only operasional |

**U02 - Audit Log**
- Semua aktivitas krusial tercatat (siapa, apa, kapan)
- Tidak bisa dihapus oleh user biasa

---

## 3. RELASI DATABASE (ERD)

### 3.1 Tabel Utama
sql -- MASTER tbl_obat (id_obat, kode_obat, nama_generik, nama_dagang, id_kategori, id_satuan, golongan, harga_beli, harga_jual, stok_minimum, is_active, created_at, updated_at)

tbl_kategori (id_kategori, nama_kategori, deskripsi)

tbl_satuan (id_satuan, nama_satuan, singkatan)

tbl_supplier (id_supplier, nama, alamat, kota, telepon, email, npwp, syarat_bayar, is_active)

tbl_pelanggan (id_pelanggan, kode_member, nama, telepon, alamat, tanggal_lahir, total_poin, is_active, created_at)

tbl_user (id_user, nama, username, password_hash, id_role, no_sipa, is_active, created_at)

tbl_role (id_role, nama_role, permissions_json)

-- STOK tbl_stok (id_stok, id_obat[FK], batch_number, expired_date, jumlah, id_pembelian[FK], created_at)

-- PEMBELIAN tbl_pembelian (id_pembelian, no_po, id_supplier[FK], tanggal_po, tanggal_terima, total, diskon, status, id_user[FK], catatan, created_at)

tbl_detail_pembelian (id, id_pembelian[FK], id_obat[FK], jumlah_pesan, jumlah_terima, harga_beli, diskon, batch_number, expired_date, subtotal)

tbl_hutang_supplier (id_hutang, id_pembelian[FK], no_faktur, tanggal_faktur, jatuh_tempo, total, sisa, status)

tbl_bayar_hutang (id_bayar, id_hutang[FK], tanggal, jumlah, metode, keterangan, id_user[FK])

-- RESEP & PENJUALAN tbl_resep (id_resep, no_resep, nama_dokter, nama_pasien, id_pelanggan[FK nullable], tanggal, status, id_user[FK], catatan)

tbl_detail_resep (id, id_resep[FK], id_obat[FK], jumlah, aturan_pakai, signa, keterangan)

tbl_transaksi (id_transaksi, no_transaksi, id_resep[FK nullable], id_pelanggan[FK nullable], tanggal, subtotal, diskon_item, diskon_global, total, bayar, kembalian, metode_bayar, poin_dipakai, poin_didapat, id_user[FK], id_shift[FK], status)

tbl_detail_transaksi (id, id_transaksi[FK], id_obat[FK], id_stok[FK], jumlah, harga_jual, diskon, subtotal)

-- KASIR tbl_shift (id_shift, id_user[FK], waktu_buka, waktu_tutup, saldo_awal, total_penjualan, saldo_akhir, selisih, status, catatan)

-- STOK OPNAME tbl_opname (id_opname, tanggal, id_user[FK], status, catatan)

tbl_detail_opname (id, id_opname[FK], id_obat[FK], id_stok[FK], stok_sistem, stok_fisik, selisih, keterangan)

tbl_adjustment (id_adj, id_obat[FK], id_stok[FK nullable], jumlah_sebelum, jumlah_sesudah, selisih, alasan, id_user[FK], tanggal)

-- LOG tbl_audit_log (id_log, id_user[FK], aksi, tabel, id_record, data_lama_json, data_baru_json, ip_address, created_at)

### 3.2 Diagram Relasi (Simplified)
SUPPLIER ──────< PEMBELIAN >────────── DETAIL_PEMBELIAN │ │ HUTANG_SUPPLIER STOK ────────< DETAIL_TRANSAKSI │ │ PELANGGAN ─────< RESEP >──── DETAIL_RESEP │ TRANSAKSI │ │ │ │ └─ LOYALTY TRANSAKSI OBAT SHIFT_KASIR │ USER/KASIR

---

## 4. ALUR PROSES (FLOW)

### 4.1 Alur Pengadaan Obat
Cek stok minimum ↓ Buat PO ke supplier ↓ Cetak / kirim PO ↓ Barang datang → Input penerimaan ↓ Verifikasi: jumlah, batch, expired date ↓ ↓ SESUAI TIDAK SESUAI → Catat selisih / retur sebagian ↓ Konfirmasi penerimaan ↓ Stok otomatis bertambah (per batch) ↓ Faktur masuk → Hutang tercatat ↓ Bayar hutang → Status hutang lunas

### 4.2 Alur Pelayanan Resep
Pasien datang dengan resep ↓ Input data resep (dokter, pasien, obat) ↓ Sistem cek ketersediaan stok ↓ ↓ TERSEDIA TIDAK TERSEDIA → Informasikan ke pasien ↓ ↓ Apoteker validasi Tawarkan obat substitusi (jika ada) ↓ Siapkan / racik obat (FEFO otomatis) ↓ Generate & cetak etiket ↓ Serahkan ke kasir ↓ Kasir proses pembayaran ↓ Stok otomatis berkurang (dari batch terlama/terdekat expired) ↓ Cetak struk → Selesai

### 4.3 Alur Transaksi OTC (Tanpa Resep)
Pelanggan minta obat ↓ Kasir/TTK search obat (nama / barcode) ↓ Tambah ke keranjang transaksi ↓ Pilih pelanggan member (opsional) ↓ Input pembayaran → Kalkulasi kembalian ↓ Konfirmasi → Stok berkurang otomatis ↓ Akumulasi poin (jika member) ↓ Cetak struk

### 4.4 Alur Stok Opname
Admin buat sesi opname baru ↓ Pilih kategori / semua obat ↓ Petugas hitung fisik & input ke sistem ↓ Sistem tampilkan perbandingan (sistem vs fisik) ↓ Review selisih oleh apoteker/admin ↓ Approve adjustment ↓ Stok di sistem diupdate → Log tersimpan ↓ Cetak laporan opname

---

## 5. STACK TEKNOLOGI (REKOMENDASI)

### 5.1 Pilihan A — Web App (Online / LAN)

| Layer | Teknologi |
|---|---|
| Backend | Laravel 11 (PHP 8.2+) |
| Frontend | Vue.js 3 + Inertia.js |
| UI Framework | Tailwind CSS + shadcn/ui |
| Database | MySQL 8 / PostgreSQL 16 |
| Cache | Redis |
| Auth | Laravel Sanctum |
| PDF | DomPDF / Browsershot |
| Print Struk | ESC/POS via PHP |
| Server | Nginx + PHP-FPM (VPS atau lokal) |

### 5.2 Pilihan B — Desktop Hybrid (Offline-first)

| Layer | Teknologi |
|---|---|
| Desktop wrapper | Electron.js atau Tauri |
| Backend | Laravel (local server) atau Node.js |
| Frontend | React / Vue |
| Database | SQLite (lokal) → sync ke MySQL pusat |
| Print | Node-escpos |

> **Rekomendasi:** Pilihan A (web app berbasis LAN) lebih mudah di-maintain, bisa diakses dari beberapa komputer di apotek tanpa install, dan backup data lebih mudah. Pilihan B lebih cocok jika apotek sering offline total.

---

## 6. KEAMANAN

- Password di-hash dengan bcrypt (tidak disimpan plain text)
- Session token dengan expired time
- Setiap aksi sensitif (void, adjustment, hapus data) butuh konfirmasi password / OTP
- HTTPS wajib jika diakses dari luar jaringan lokal
- Backup database otomatis harian
- Audit log tidak bisa dihapus oleh siapapun kecuali super admin dengan prosedur khusus
- Rate limiting pada endpoint login (anti brute force)

---

## 7. REGULASI & KEPATUHAN

| Hal | Ketentuan |
|---|---|
| Narkotika & Psikotropika | Wajib dicatat per transaksi, laporan bulanan ke BPOM via SIPNAP |
| Obat Keras | Harus ada resep dokter, dicatat nama dokter & pasien |
| SIPA Apoteker | Nomor SIPA tampil di struk dan laporan |
| Kartu Stok | Sistem otomatis generate kartu stok digital per obat |
| Expired Date | Sistem cegah penjualan obat yang sudah expired |

---

## 8. KEBUTUHAN NON-FUNGSIONAL

| Aspek | Target |
|---|---|
| Performa | Transaksi kasir < 2 detik response |
| Uptime | 99% (jika web, server lokal) |
| Concurrent user | Minimal 5 user bersamaan |
| Backup | Otomatis harian, simpan 30 hari terakhir |
| Skalabilitas | Bisa upgrade ke multi-cabang di fase berikutnya |
| Browser support | Chrome, Edge, Firefox (versi terbaru) |

---

## 9. FASE PENGEMBANGAN

### Fase 1 — Core (2–3 bulan)
- Setup project & database
- Modul master data
- Modul stok & pengadaan
- Modul kasir / POS dasar
- Modul user & hak akses
- Laporan penjualan dasar

### Fase 2 — Lengkap (1–2 bulan)
- Modul resep & etiket
- Modul hutang supplier
- Laporan keuangan
- Stok opname
- Alert & notifikasi
- Laporan narkotika/psikotropika

### Fase 3 — Enhancement (1 bulan)
- Loyalty pelanggan
- Dashboard & grafik
- Backup otomatis
- Audit log lengkap
- Optimasi performa & UI

---

## 10. ESTIMASI RESOURCE

| Item | Keterangan |
|---|---|
| Developer Backend | 1 orang (full stack lebih baik) |
| Developer Frontend | 1 orang (bisa digabung jika full stack) |
| Duration | 4–6 bulan untuk versi production-ready |
| Server/Hosting | VPS lokal atau cloud (minimal 2 core, 4GB RAM) |
| Hardware apotek | PC/laptop + thermal printer + barcode scanner (opsional) |

---

## 11. OPEN POINTS (Perlu Keputusan)

- [ ] Apakah perlu fitur barcode scanner untuk input obat?
- [ ] Apakah perlu multi harga jual (eceran vs grosir)?
- [ ] Apakah PPN perlu ditangani di aplikasi?
- [ ] Apakah perlu fitur konsultasi / chat apoteker online?
- [ ] Skema backup: lokal saja atau ke cloud?
- [ ] Apakah ada integrasi dengan timbangan digital (untuk obat racik)?
- [ ] Bahasa antarmuka: Indonesia saja atau bilingual?

---

*Dokumen ini adalah draft awal untuk evaluasi. Setiap bagian dapat disesuaikan berdasarkan kebutuhan spesifik apotek.*
---

