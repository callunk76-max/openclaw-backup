# Riset Aplikasi Apotek Puskesmas se-Indonesia

Dibikin: 11 Mei 2026
Sumber: Riset web, Hashmicro, Vmedis, ePuskesmas, SAFFMedic, ApotekDigital, SIMFAR, SIMPUS

---

## Daftar Aplikasi yang Ditemukan

| Nama | Tipe | Target | Harga |
|------|------|--------|-------|
| **ePuskesmas** | Web/Cloud | Puskesmas (resmi Kemenkes) | Gratis (pemerintah) |
| **Vmedis** | Cloud + Mobile | Apotek swasta | Rp99-199rb/bulan |
| **ApotekDigital** | Cloud | Apotek, Klinik, Puskesmas | Berbayar |
| **SAFFMedic** | Web (SIMRS) | RS & Klinik | Berbayar |
| **SIMFAR/SIMPUS** | Desktop/Web | Puskesmas (lokal) | Variatif |
| **Apotek.ai** | Cloud | Apotek | Berbayar |

---

## Daftar Fitur (dari semua aplikasi yang diriset)

### A. Manajemen Obat & Stok
- [ ] Input data obat (nama, golongan, kategori, satuan)
- [ ] Katalog obat dengan barcode / scan barcode
- [ ] Kartu stok otomatis (setiap mutasi tercatat)
- [ ] Stok opname (mobile support)
- [ ] Manajemen batch & tanggal kadaluarsa (ED)
- [ ] Peringatan obat mendekati expired (3/6/12 bln)
- [ ] Multi gudang / rak penyimpanan
- [ ] Obat racikan (formula racik, kalkulasi harga)
- [ ] Retur obat (ke supplier / rusak)

### B. Transaksi & Penjualan
- [ ] POS / Kasir
- [ ] Cetak struk otomatis
- [ ] Penjualan resep (resep dokter)
- [ ] Penjualan non-resep (bebas)
- [ ] Diskon & promo
- [ ] Multi metode pembayaran (tunai, non-tunai, BPJS)
- [ ] Pajak (PPN otomatis)
- [ ] Sistem shift kasir

### C. Pembelian & Pengadaan
- [ ] Purchase Order (PO)
- [ ] Penerimaan barang
- [ ] Analisa supplier (diskon, histori)
- [ ] Smart forecasting / rekomendasi stok
- [ ] Analisa Pareto (obat 80:20)
- [ ] Auto reorder point

### D. Resep & Pelayanan Farmasi
- [ ] Entry resep dari dokter
- [ ] E-resep (digital)
- [ ] Copy resep
- [ ] Obat racikan (puyer, kapsul, salep, dll)
- [ ] Konseling obat / informasi obat
- [ ] Riwayat resep pasien
- [ ] Interaksi obat (drug interaction check)
- [ ] Label obat / etiket

### E. Pasien & Rekam Medis
- [ ] Registrasi pasien (identitas, alamat, BPJS)
- [ ] Rekam medis elektronik (EMR)
- [ ] Riwayat kunjungan & pengobatan
- [ ] Alergi & kontraindikasi
- [ ] Modul KIA (Kesehatan Ibu & Anak)
- [ ] Imunisasi
- [ ] Modul KB

### F. Laporan & Analisa
- [ ] Laporan penjualan harian/mingguan/bulanan
- [ ] Laporan stok (mutasi, opname, expired)
- [ ] Laporan keuangan (laba/rugi, arus kas)
- [ ] Laporan PPN
- [ ] Laporan khusus puskesmas (SP2TP, SKDR, Profil)
- [ ] Dashboard real-time
- [ ] Grafik & analisa tren

### G. Integrasi & Kepatuhan
- [ ] Integrasi SATUSEHAT (FHIR)
- [ ] Integrasi dengan ePuskesmas / SIMPUS
- [ ] Integrasi BPJS
- [ ] Integrasi dengan Dinkes Kab/Kota
- [ ] Export data (Excel, PDF, CSV)

### H. Fitur Pendukung
- [ ] Multi user & hak akses (admin, apoteker, kasir)
- [ ] Multi cabang / unit
- [ ] Backup & restore data
- [ ] Notifikasi (expired, stok menipis)
- [ ] Manajemen keuangan (jurnal, biaya operasional)
- [ ] Mobile version (stok opname via HP)
- [ ] Offline mode (tetap jalan tanpa internet)

---

## Poin Penting

1. **ePuskesmas** adalah sistem resmi dari Kemenkes — wajib dipake puskesmas buat laporan. Kalo bikin apotik sendiri, mesti bisa integrasi/nyambung ke sini.
2. **Vmedis** paling banyak dipake apotek swasta (4000+ pengguna) — fiturnya matang, fokus anti-bocor.
3. **SATUSEHAT** sekarang wajib — semua faskes harus kirim data pake standar FHIR.
4. **Yang belum banyak di-adopt:** AI/analytics, prediksi stok pake machine learning, sistem antrian online.
5. **Potensi gap di pasaran:** Aplikasi puskesmas farmasi yang modern, open-source atau custom, dengan integrasi SATUSEHAT bawaan.

---

## Mau lanjut kemana? (Diskusi Besok)
- ~~Bikin struktur database~~
- ~~Flowchart / user flow~~
- ~~Tech stack pilihan~~
- ~~Roadmap MVP~~
