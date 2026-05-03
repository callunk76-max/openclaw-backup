# STANDAR OPERASIONAL PROSEDUR
## PENGELOLAAN LOG ACTIVITY
### LPSE KABUPATEN BULUKUMBA

---

**Nomor SOP :** SOP-LPSE-BLK-11-002  
**Tanggal Pembuatan :** April 2025  
**Tanggal Revisi :** -  
**Tanggal Efektif :** April 2025  
**Disahkan oleh :** Kepala LPSE Kabupaten Bulukumba  

---

## 1. TUJUAN
Mengatur tata cara pengelolaan log activity sistem LPSE Kabupaten Bulukumba untuk memastikan keamanan dan auditabilitas sistem.

## 2. RUANG LINGKUP
SOP ini berlaku untuk seluruh log yang dihasilkan oleh sistem LPSE Kabupaten Bulukumba, meliputi:
- Log akses aplikasi SPSE
- Log akses server
- Log akses personil LPSE
- Log sistem operasi

## 3. PROSEDUR

### 3.1 Pengumpulan Log
1. Sistem secara otomatis mencatat seluruh aktivitas ke dalam log
2. Log disimpan di server dengan kapasitas yang memadai
3. Log dirotasi secara otomatis setiap hari untuk mencegah penuhnya storage

### 3.2 Pemantauan Log
1. Admin sistem memantau log setiap hari kerja
2. Pemantauan difokuskan pada:
   - Login gagal berulang (brute force)
   - Akses di luar jam kerja
   - Akses dari IP yang tidak dikenal
   - Perubahan konfigurasi sistem
   - Aktivitas yang tidak wajar (anomali)
3. Jika ditemukan aktivitas mencurigakan, segera dilaporkan kepada Kepala LPSE

### 3.3 Backup Log
1. Log dibackup setiap minggu bersamaan dengan backup data
2. Backup log disimpan minimal selama 1 (satu) tahun
3. Berita Acara Backup Log dibuat setiap bulan

### 3.4 Pelaporan
1. Admin sistem membuat laporan pemantauan log setiap bulan
2. Laporan mencakup: ringkasan aktivitas, temuan anomali, dan tindak lanjut
3. Laporan disampaikan kepada Kepala LPSE

### 3.5 Pencatatan
Hasil pemantauan log dicatat dalam **Berita Acara Pemantauan Log Activity (BA-LPSE-BLK-11-002)**

## 4. INDIKATOR ANOMALI
Berikut adalah kondisi yang dianggap anomali dan harus segera ditindaklanjuti:

| Indikator | Ambang Batas | Tindakan |
|-----------|-------------|---------|
| Login gagal | > 5 kali dalam 10 menit | Blokir IP, lapor ke Kepala LPSE |
| Akses di luar jam kerja | Setiap kejadian | Verifikasi ke personil terkait |
| Transfer data besar | > 1 GB dalam sekali transfer | Investigasi segera |
| Akses dari IP asing | Setiap kejadian | Blokir dan investigasi |

---

**Ditetapkan di :** Bulukumba  
**Pada tanggal :** April 2025  

**Kepala LPSE Kabupaten Bulukumba**

**[NAMA KEPALA LPSE]**  
NIP. [NIP]
