# STANDAR OPERASIONAL PROSEDUR
## BACKUP DAN RESTORE DATA
### LPSE KABUPATEN BULUKUMBA

---

**Nomor SOP :** SOP-LPSE-BLK-11-001  
**Tanggal Pembuatan :** April 2025  
**Tanggal Revisi :** -  
**Tanggal Efektif :** April 2025  
**Disahkan oleh :** Kepala LPSE Kabupaten Bulukumba  

---

## 1. TUJUAN
Mengatur tata cara backup dan restore data LPSE Kabupaten Bulukumba untuk memastikan ketersediaan dan integritas data.

## 2. RUANG LINGKUP
SOP ini berlaku untuk seluruh data yang dikelola oleh LPSE Kabupaten Bulukumba, meliputi:
- Database aplikasi SPSE
- Data file dokumen pengadaan
- Konfigurasi sistem
- Log sistem

## 3. JADWAL BACKUP

| Jenis Backup | Frekuensi | Waktu Pelaksanaan | Media Penyimpanan |
|-------------|-----------|-------------------|-------------------|
| Backup Harian | Setiap hari | Pukul 23.00 WITA | Server Cadangan |
| Backup Mingguan | Setiap Senin | Pukul 01.00 WITA | Server Cadangan + External HDD |
| Backup Bulanan | Tanggal 1 | Pukul 01.00 WITA | Server Cadangan + External HDD |

## 4. PROSEDUR BACKUP

### 4.1 Backup Otomatis (Scheduled)
1. Sistem melakukan backup otomatis sesuai jadwal yang telah dikonfigurasi
2. Admin sistem memverifikasi hasil backup setiap pagi hari
3. Jika backup gagal, admin sistem segera melakukan backup manual
4. Hasil backup dicatat dalam **Form Log Backup (F-LPSE-BLK-11-001)**
5. Berita Acara Hasil Backup dibuat setiap bulan

### 4.2 Backup Manual
1. Admin sistem melakukan backup manual jika diperlukan (sebelum update sistem, dll)
2. Backup manual dicatat dalam Form Log Backup dengan keterangan "Manual"
3. Admin sistem memverifikasi integritas data hasil backup

### 4.3 Verifikasi Backup
1. Admin sistem melakukan verifikasi backup minimal 1 kali per minggu
2. Verifikasi dilakukan dengan mengecek ukuran file dan timestamp backup
3. Secara berkala (minimal 1 kali per bulan) dilakukan restore test untuk memastikan backup dapat dipulihkan

## 5. PROSEDUR RESTORE

### 5.1 Kondisi yang Memerlukan Restore
- Kerusakan data akibat kegagalan sistem
- Serangan siber (ransomware, dll)
- Kesalahan penghapusan data
- Pengujian pemulihan (restore test)

### 5.2 Langkah Restore
1. Admin sistem melaporkan kebutuhan restore kepada Kepala LPSE
2. Kepala LPSE memberikan persetujuan restore
3. Admin sistem mengidentifikasi backup yang akan digunakan (tanggal/versi)
4. Admin sistem melakukan restore pada lingkungan test terlebih dahulu
5. Setelah dipastikan berhasil, restore dilakukan pada sistem produksi
6. Admin sistem memverifikasi integritas data setelah restore
7. Hasil restore didokumentasikan dengan screenshot dan **Berita Acara Restore**

## 6. DAFTAR DATA YANG DIBACKUP

| No | Jenis Data | Lokasi Sumber | Ukuran Estimasi | Prioritas |
|----|-----------|---------------|-----------------|-----------|
| 1  | Database SPSE | /var/lib/mysql | ~10 GB | Tinggi |
| 2  | File dokumen pengadaan | /data/spse/files | ~50 GB | Tinggi |
| 3  | Konfigurasi sistem | /etc/ | ~100 MB | Menengah |
| 4  | Log sistem | /var/log/ | ~5 GB | Rendah |

---

**Ditetapkan di :** Bulukumba  
**Pada tanggal :** April 2025  

**Kepala LPSE Kabupaten Bulukumba**

**[NAMA KEPALA LPSE]**  
NIP. [NIP]
