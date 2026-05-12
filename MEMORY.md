# Long Term Memory

- **Trading Bot Watchlist Command**: If Callunk sends a message like `/OpenPosisi [PAIR] [BUY/SELL/CLOSE]` (e.g. `/OpenPosisi AUDUSD BUY`), I must parse the command and execute `python3 /root/.openclaw/workspace/Trading/manage_positions.py [PAIR] [ACTION]` to update the active tracking list.

## Apotik Aramedica (MK - Farmasi)

**Pengganti MK (Mokidonut/Apotik PKM Ujung Loe)**
- **URL:** `callunk.my.id/mk/`
- **Port:** 5001, Gunicorn via systemd (`mokidonut.service`)
- **Service restart:** `systemctl restart mokidonut`
- **Framework:** Flask + SQLAlchemy + SQLite (WAL mode)
- **Blueprint structure:** routes/auth, dashboard, master, stok, pembelian, resep, kasir, laporan
- **Template filter:** `format_tgl` (tgl Indonesia), `format_rp` (Rp)
- **Golongan obat:** Bebas, Bebas Terbatas, Keras, Narkotika, Psikotropika
- **FEFO:** Transaksi ambil stok dari batch expired terdekat
- **Login default:** admin/admin123, kasir/kasir123, apoteker/apoteker123
- **Auth:** Session-based, nginx rewrite cookie path ke `/mk/`
- **All internal links MUST use `/mk/` prefix** (nginx subpath proxy)
- **Mobile:** Sidebar otomatis berubah jadi hamburger menu (☰) di HP via CSS @media + JS toggle
- **UI Components:**
  - All searchable dropdowns use **Select2** (Bootstrap 5 theme) — add class `select-search`
  - Select2 init in base.html, reinit di dynamic rows pake `$(row).find('.select-search').select2({...})`
  - **Autocomplete search** di setiap halaman list (obat, stok, resep) dengan debounce 500ms + icon search + X button untuk clear
  - **Breadcrumb navigation** (`{% from "base.html" import breadcrumb %}{{ breadcrumb(...) }}`) di semua sub-menu — setiap halaman form/detail ada tombol Kembali (`bi-arrow-left`)
  - Forms pakai Bootstrap 5 + manual responsive CSS + input-group Rp untuk harga
  - Buttons: `bi-plus-lg` untuk tambah, `bi-pencil` edit, `bi-trash` hapus, `bi-x-lg` batal/tutup
  - Flash messages auto-hide 5 detik

## SIRUP Bulukumba App

**CRITICAL: App runs on GUNICORN, not Flask dev server!**
- Port: 5005, served via nginx at callunk.my.id/
- Gunicorn command: `cd /root/.openclaw/workspace/App/sirup_bulukumba && gunicorn -w 4 -b 127.0.0.1:5005 --timeout 120 --access-logfile - --error-logfile - app:app`
- Template: `templates/index.html`
- After editing templates, MUST restart gunicorn: `kill $(lsof -ti:5005) && sleep 2 && cd /root/.openclaw/workspace/App/sirup_bulukumba && gunicorn -w 4 -b 127.0.0.1:5005 --timeout 120 --access-logfile - --error-logfile - app:app </dev/null > /dev/null 2>&1 &`
- NO systemd service active (healthcheck.sh exists but unused)