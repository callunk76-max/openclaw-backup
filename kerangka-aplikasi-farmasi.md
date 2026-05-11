# Kerangka Aplikasi Farmasi Puskesmas

## 1. 🎯 Visi & Tujuan

Aplikasi manajemen farmasi puskesmas yang **sederhana, cepat, dan sesuai realita Puskesmas di Kab. Bulukumba**. Bukan super-app — fokus ke **pelayanan kefarmasian** saja.

---

## 2. 👥 Aktor & Peran

| Aktor | Peran | Level Akses |
|-------|-------|-------------|
| **Petugas Farmasi / Apoteker** | Entry resep, dispensing, stok opname | Penuh |
| **Dokter / Perawat** | Lihat riwayat obat pasien | Terbatas |
| **Kepala Puskesmas** | Laporan, monitoring | Read-only + laporan |
| **Dinkes Kabupaten** | Monitoring ketersediaan obat | Laporan saja |
| **Pasien** | Lihat riwayat (via antrian/nomor) | Minimal |

---

## 3. 📐 Alur Pelayanan Farmasi (Flow)

```
[Dokter Periksa] → Resep (digital/tulis) 
       ↓
[Farmasi Terima Resep]
       ├── Entry / Scan Resep 
       ├── Validasi (alergi, duplikasi, interaksi)
       └── Cek Stok
              ↓
       [Obat Tersedia] → Siapkan & Label → Serahkan ke Pasien
              ↓
       [Obat Tidak Tersedia] → Catat di buku kosong / Resep ditunda
              ↓
       [BPJS / Jaring Lindung / Umum] → Catat jaminan
              ↓
       [Laporan Obat Keluar] → Update stok otomatis
```

---

## 4. 🗂️ Modul Inti

### A. Modul OBAT (Seed Data — Gak Perlu Input)
```
┌─ Database Obat Puskesmas ─────────────────────────┐
│  • Nama Generik (wajib)                           │
│  • Nama Dagang (opsional — bisa banyak per generik)│
│  • Golongan (bebas, terbatas, narkotik, psikotropik)│
│  • Bentuk Sediaan (tab, kaps, sir, inj, cream)     │
│  • Kekuatan (500 mg, 250 mg/5 mL, dll)             │
│  • Satuan (tab, btl, amp, box)                     │
│  • FORNAS / Non-FORNAS                             │
│  • E-Katalog Reference                             │
│  • Harga Eceran (acuan)                            │
└──────────────────────────────────────────────────┘
        ↓ User cukup search & klik
   [Search Bar: "amoksi" → muncul Amoksisilin 250mg, 500mg, Sir]
```

### B. Modul RESEP / PELAYANAN
```
┌─ Resep ────────────────────────────────────────────┐
│  • No. Resep (auto)                                │
│  • Tanggal & Waktu                                 │
│  • Pasien: Nama, No. BPJS/KTP, Alamat              │
│  • Dokter pengirim (pilih dari daftar)             │
│  • Diagnosa (opsional)                             │
│  • Obat: [search + pilih + jumlah + aturan pakai]  │
│  • Racikan? Ya/Tidak                               │
│    ├── Komponen racikan (pilih obat + jumlah)      │
│    ├── Aturan pakai racikan (pagi/siang/malam)     │
│    └── Signa / etiket racikan (puyer/kapsul/crm)   │
│  • Jaminan: BPJS / Jamkesda / Umum / Lainnya       │
│  • Status: Baru / Siap / Diambil / Ditunda         │
└──────────────────────────────────────────────────┘
```

### C. Modul STOK & GUDANG (Obat + BHP)

```
┌─ Manajemen Stok ──────────────────────────────────┐
│  • Penerimaan dari **Gudang Farmasi Dinkes Kab**   │
│  • Pengeluaran (otomatis dari pelayanan)           │
│  • Stok Opname (mobile-friendly)                   │
│  • Peringatan: Stok Minimum & ED (Expired)         │
│  • Kartu Stok (riwayat lengkap per item)           │
│                                                    │
│  Item: OBAT (generik/kekuatan/sediaan)             │
│        BHP (kasa, kapas, spuit, sarung tn, dll)   │
│                                                    │
│  ┌── Distribusi ke Unit Bawah ──────────────────┐  │
│  │  • Pustu (Puskesmas Pembantu)                │  │
│  │  • Polindes (Pondok Bersalin Desa)           │  │
│  │  • Poskesdes (Pos Kesehatan Desa)            │  │
│  │  • Posyandu                                   │  │
│  │  └── Catat: [Unit] ambil [Item] [Jumlah]     │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### C2. Supply Chain Lengkap

```
Gudang Farmasi Dinkes Kabupaten
  │
  ├──→ Distribusi Obat + BHP ke Puskesmas (periodik / permintaan)
  │
  ▼
Puskesmas (Gudang Farmasi Puskesmas)
  │
  ├──→ Pelayanan Resep + Tindakan (obat keluar)
  ├──→ Distribusi ke Pustu / Polindes / Poskesdes
  ├──→ Distribusi ke Posyandu
  │
  └──→ Laporan Pemakaian ke Dinkes (LPLPO — periodik)
          ↑
Pustu / Unit laporkan pemakaian periodik ke Puskesmas
```

**Fitur Distribusi & Rantai Pasok:**
- Catat permintaan & penerimaan dari Gudang Farmasi Kabupaten
- Catat distribusi ke Pustu/Polindes/Poskesdes (nama unit, item, jumlah, tanggal)
- Setiap unit laporkan pemakaian periodik (mingguan/bulanan)
- Sisa stok di setiap unit bisa terpantau
- **LPLPO** = Laporan Pemakaian & Lembar Permintaan Obat — format standar Dinkes
- Laporan gabungan: Pemakaian Puskesmas + seluruh Pustu untuk dikirim ke Dinkes

### D. Modul JAMINAN & BIAYA
```
┌─ Jaminan ──────────────────────────────────────────┐
│  • BPJS Kesehatan (PBI / Mandiri / PPU)            │
│  • Jamkesda / Jaring Lindung                       │
│  • Umum / Tunai                                    │
│  • Catat: No. SEP, No. Kartu, Faskes perujuk       │
│  • Hitung: biaya obat → ditanggung / iur biaya     │
└──────────────────────────────────────────────────┘
```

### E. Modul LAPORAN
```
┌─ Laporan ──────────────────────────────────────────┐
│  •L-1: Obat Keluar Harian (rekapitulasi peresepan) │
│  •L-2: LPLPO (Laporan Pemakaian & Lembar Permintaan│
│        Obat) — format Dinkes                       │
│  •L-3: Stok Opname (fisik vs sistem)               │
│  •L-4: Obat Hampir Expired & Stagnan               │
│  •L-5: Pelayanan per Jaminan (BPJS/Jamkesda/Umum)  │
│  •L-6: 10 Besar Penyakit + Obatnya                 │
│  •Export: Excel / PDF untuk laporan ke Dinkes      │
└──────────────────────────────────────────────────┘
```

---

## 5. 🔗 Integrasi (Realistis)

| Integrasi | Prioritas | Status |
|-----------|-----------|--------|
| **SATUSEHAT** (FHIR) | 🔥 Nanti | Butuh registrasi resmi, pikirkan belakangan |
| **BPJS / VClaim** | 🔥 Wajib | Catat manual dulu — SEP, No. Kartu, dll |
| **E-Katalog LKPP** | ⭐ Bagus | Referensi harga & ketersediaan |
| **WhatsApp / Notifikasi** | ⭐ Bagus | Sederhana — ingetin pasien ambil obat |

> **Catatan**: ePuskesmas belum ada di Bulukumba. Fokus ke aplikasi mandiri dulu. Integrasi SATUSEHAT & BPJS pake mekanisme export/import sederhana.

---

## 6. 🖥️ Tampilan (Kira-kira)

### Halaman Utama (Dashboard)
```
┌─────────────────────────────────────┐
│ 🏠 Puskesmas X | Farmasi           │
│ ─────────────────────────────────── │
│ [🔍 Cari Obat / Pasien]            │
│                                      │
│ 📋 Antrian Resep Hari Ini: 12      │
│ ⏳ Menunggu: 5  ✅ Selesai: 7      │
│                                      │
│ ⚠️ Stok Kritis: 3 obat             │
│ 📅 ED Bulan Ini: 2 obat            │
│                                      │
│ [+] Resep Baru   [📊 Laporan]      │
└─────────────────────────────────────┘
```

### Form Entry Resep
```
┌─ Entry Resep ──────────────────────┐
│ Pasien: [___________] No.BPJS: [__]│
│ Dokter: [Dropdown nama dokter]     │
│ Jaminan: [BPJS | Jamkesda | Umum]  │
│                                     │
│ Obat 1: [amoks] → Amoksisilin 500mg│
│   Jumlah: [10] Aturan: [3x1]       │
│ Obat 2: [___________] + [Tambah]   │
│                                     │
│ [Simpan] [Cetak Label]             │
└─────────────────────────────────────┘
```

---

## 7. 📦 Tech Stack (Usulan)

| Lapisan | Pilihan | Alasan |
|---------|---------|--------|
| **Backend** | Flask / Python (seperti SIRUP) | Lo udah familiar |
| **Frontend** | HTML + JS (pake Tailwind/HTMX) | Sederhana, gak perlu SPA |
| **Database** | SQLite (awal) → PostgreSQL | SQLite gampang, PostgreSQL kalo udah besar |
| **Deploy** | VM callunk.my.id | Udah jalan & ada nginx |
| **Search** | SQL LIKE / FTS (awal) → Meilisearch (opsional) | Cukup buat drug search |

---

## 8. ⚠️ Realita di Lapangan (Catetan)

1. **Jaringan** — Puskesmas di pelosok Bulukumba kadang lemot / mati lampu → perlu offline mode
2. **Literasi Digital** — Gak semua petugas farmasi familiar komputer → UI harus simpel banget
3. **BPJS** — Klaim BPJS butuh SEP (Surat Eligibilitas Peserta) dan verifikasi manual
4. **Gudang Farmasi Kabupaten** — Sumber semua obat & BHP. Kalo di gudang kosong, ya kosong. Distribusi periodik berdasarkan permintaan (LPLPO)
5. **BHP** — Bahan Habis Pakai (kasa, kapas, spuit, sarung tangan, alkohol swab, dll) juga dikelola sama — aturan stoknya sama kayak obat
6. **Birokrasi** — Integrasi SATUSEHAT butuh proses panjang, gak bisa langsung
7. **Laporan Dinkes** — Laporan periodik ke Dinkes via LPLPO. Masih sering Excel manual → kita harus bisa export
8. **ePuskesmas** — Belum ada di Bulukumba. Fokus ke aplikasi mandiri dulu

---

## 9. 🔥 Prioritas MVP

| Prioritas | Fitur |
|-----------|-------|
| **P1** | Entry resep + search obat dari database FORNAS |
| **P1** | **Racikan** (komponen racikan, etiket, kalkulasi harga) |
| **P1** | Catat jaminan (BPJS / Jamkesda / Umum) |
| **P1** | Stok keluar otomatis dari pelayanan |
| **P2** | Distribusi obat ke Pustu / Polindes / Poskesdes |
| **P2** | Laporan pemakaian dari unit bawah (periodik) |
| **P2** | Laporan LPLPO format Excel |
| **P2** | Penerimaan stok + stok opname |
| **P2** | Peringatan expired & stok minimal |
| **P3** | Multi-user / hak akses |
| **P3** | Export data SATUSEHAT |
| **P4** | Dashboard + grafik |
| **P4** | Offline mode |

---

**Catatan**: Ini kerangka awal. Masih banyak yang bisa diutak-atik — struktur database, detail alur BPJS, format laporan Dinkes yg bener, dll. Mana yang pengen lo bahas duluan? 😎
