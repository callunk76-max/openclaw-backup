# Work Log Automation - dikerja.com

## Credentials
- Username: 197607121997021001
- Password: x1x2x3x4

## Workflow
1. Login to https://dikerja.com
2. Navigate to 'Aktifitas' menu (left side of dashboard)
3. Click 'Tambah Data'
4. Input:
   - Tanggal: Current workday
   - Sasaran Kinerja: "non sasaran"
   - Hasil: 1
   - Satuan & Kegiatan: Default
   - Nama Aktivitas: Match/Synchronize with the provided descriptions (Refer to history for cheat sheet)
   - Keterangan: Input all of the following descriptions daily:
     * Melakukan cek harian terhadap layanan Helpdesk LPSE Kab. Bulukumba
     * Membantu tim verifikasi melakukan pelayanan pada penyedia atau user LPSE
     * Melakukan layanan konsultasi pengadaan lainnya
     * Melaksanakan pelayanan lainnya pada LPSE
     * Melakukan cek harian terhadap kondisi server, layanan jaringan dan infrastruktur LPSE Kab.Bulukumba
     * Memeriksa apakah ada instruksi-instruksi dari Adminstrator LKPP Pusat
     * Memeriksa kembali data backup dari server LPSE

## Execution Logic
- Trigger: Daily at 15:00.
- Process: 
  1. Ask user "Ready to fill activity?".
  2. If user says "Yes", execute all entries for the day.
  3. Confirm completion to user.

## Notes
- Use history of previous days as a reference for selecting the most appropriate "Nama Aktivitas".
