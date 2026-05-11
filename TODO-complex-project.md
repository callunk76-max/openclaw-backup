# Todo List — Project NOMAD & Complex Build

Dibikin: Senin, 11 Mei 2026
Source: Research NOMAD + brainstorming ama Callunk

---

## ✅ Selesai
- [x] Riset Crosstalk Solutions (perusahaan VoIP & networking)
- [x] Riset Project NOMAD (offline survival computer, Docker stack)
- [x] Cek Docker di VM → gak ada, perlu install dulu
- [x] Catat komponen utama NOMAD: Ollama, Kiwix, OpenStreetMap, Kolibri
- [x] Catat perbandingan kompetitor (PrepperDisk, Doom Box, R.E.A.D.I.)

---

## 📋 Rencana Ke Depan

### Phase 1: Infrastructure
- [ ] Install Docker + Docker Compose di VM
- [ ] Setup Nginx reverse proxy biar semua service rapi di callunk.my.id
- [ ] Siapkan storage buat zim files + maps data

### Phase 2: Services
- [ ] **Kiwix (Wikipedia offline)** — serve Wikipedia + WikiHow + medical refs via callunk.my.id
- [ ] **OpenStreetMap offline** — maps daerah Sulsel/Bulukumba
- [ ] **Kolibri (Khan Academy)** — kalo relevan buat edukasi offline
- [ ] Integrasi dengan SIRUP Bulukumba app yang udah jalan

### Phase 3: Command Center
- [ ] Bikin unified dashboard / portal sendiri
  - Link ke SIRUP app
  - Link ke Wikipedia offline
  - Link ke AI chat (via Ollama)
  - Link ke maps
- [ ] Single entry point di callunk.my.id

### Phase 4: Advanced
- [ ] Integrasi Ollama lokal dengan workspace (bisa nambahin konteks file-file)
- [ ] Custom AI assistant yang paham konteks Callunk + project-projectnya
- [ ] Mungkin hybrid — pake Ollama buat chat ringan, pake Cuy buat eksekusi

---

## 💡 Catatan

- Ollama udah ada di laptop Callunk — gak perlu install ulang
- Kiwix dan zimbot gampang diinstall tanpa Docker kalo mau jalan sendiri
- NOMAD lisensi Apache 2.0, bebas dipake & dimodifikasi
- Comparison table di projectnomad.us ([comparison]) -- NOMAD unggul di GPU-Accelerated AI, full content library, true open source
