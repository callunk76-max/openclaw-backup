#!/usr/bin/env python3
"""Hitung batas usia pensiun (BUP) pegawai berdasarkan jabatan."""
import json, re
from datetime import datetime

DATA_FILE = "/root/.openclaw/workspace/peg_dashboard/pegawai.json"
TAHUN_INI = datetime.now().year

def tentukan_bup(jabatan, gol_kode=""):
    """
    Tentukan Batas Usia Pensiun berdasarkan jabatan.
    - Eselon II (Kadis, Sekda, Asisten, Staf Ahli, Inspektur) → 60 tahun
    - Selain Eselon II → 58 tahun
    """
    j = jabatan.upper() if jabatan else ""
    
    # === ESELON II (PIMPINAN TINGGI) → 60 ===
    eselon2 = [
        'KEPALA DINAS', 'KEPALA BADAN',
        'SEKRETARIS DAERAH',
        'STAF AHLI'
    ]
    for p in eselon2:
        if p in j and 'SUB' not in j:
            return 60
    
    # Asisten Setda (bukan JF Asisten Apoteker)
    if (' ASISTEN ' in j or j.startswith('ASISTEN ')) and 'JF ' not in j:
        return 60
    
    # Inspektur (bukan Inspektur Pembantu)
    if j == 'INSPEKTUR' or j.startswith('INSPEKTUR DAERAH') or j.startswith('PLT INSPEKTUR'):
        return 60
    
    # === NON-ESELON II → 58 ===
    return 58


def hitung_usia(tgl_lahir_str):
    """Hitung usia dari tanggal lahir (YYYY-MM-DD)."""
    if not tgl_lahir_str or tgl_lahir_str.count('-') != 2:
        return None, None
    
    try:
        parts = tgl_lahir_str.split('-')
        tahun = int(parts[0])
        bulan = int(parts[1])
        hari = int(parts[2])
        
        # Simple age calculation
        usia = TAHUN_INI - tahun
        if bulan > datetime.now().month:
            usia -= 1
        
        usia_bulan = (TAHUN_INI - tahun) * 12 + (datetime.now().month - bulan)
        
        return usia, usia_bulan
    except:
        return None, None


def hitung_semua():
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    stats = {"58": 0, "60": 0, "65": 0}
    kategori = {"Sudah Pensiun": 0, "Aman": 0, "Dekat Pensiun (<5 thn)": 0, "Segera Pensiun (<2 thn)": 0, "Unknown": 0}
    
    for a in data:
        for e in a['pegawai']:
            tgl_lahir = e.get('tgl_lahir', '')
            jabatan = e.get('jabatan', '')
            gol_kode = e.get('golongan_kode', '')
            
            usia, usia_bulan = hitung_usia(tgl_lahir)
            bup = tentukan_bup(jabatan, gol_kode)
            
            if usia is not None:
                sisa_tahun = bup - usia
                e['usia'] = usia
                e["bup"] = bup; tahun_lahir = int(tgl_lahir.split("-")[0]) if tgl_lahir and tgl_lahir.count("-") == 2 else 0; e["tahun_pensiun"] = tahun_lahir + bup if tahun_lahir else None
                e['sisa_pensiun'] = round(sisa_tahun, 1)
                
                if sisa_tahun <= 0:
                    e["status_pensiun"] = "Sudah Pensiun"; kategori["Sudah Pensiun"] = kategori.get("Sudah Pensiun", 0) + 1
                    kategori["Segera Pensiun (<2 thn)"] += 1
                elif sisa_tahun <= 2:
                    e['status_pensiun'] = "Segera Pensiun"
                    kategori["Segera Pensiun (<2 thn)"] += 1
                elif sisa_tahun <= 5:
                    e['status_pensiun'] = "Dekat Pensiun"
                    kategori["Dekat Pensiun (<5 thn)"] += 1
                else:
                    e['status_pensiun'] = "Aman"
                    kategori["Aman"] += 1
                
                stats[str(bup)] = stats.get(str(bup), 0) + 1
            else:
                e['usia'] = None
                e["bup"] = None; e["tahun_pensiun"] = None
                e['sisa_pensiun'] = None
                e['status_pensiun'] = "Unknown"
                kategori["Unknown"] += 1
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("=== ANALISIS USIA PENSIUN PNS ===")
    print(f"\nBerdasarkan UU No. 20 Tahun 2023 tentang ASN")
    print(f"(Tahun ini: {TAHUN_INI})")
    print(f"\n--- Distribusi BUP ---")
    for bup, count in sorted(stats.items()):
        print(f"  BUP {bup} tahun: {count} pegawai")
    
    print(f"\n--- Kategori ---")
    for kat, count in kategori.items():
        bar = '█' * (count // 10)
        print(f"  {kat:25s}: {count:4d} {bar}")
    
    # Show some near-retirement examples
    print(f"\n--- Contoh Pegawai Mendekati Pensiun ---")
    semua = []
    for a in data:
        for e in a['pegawai']:
            if e.get('usia') and e.get('sisa_pensiun') is not None:
                semua.append((e.get('sisa_pensiun', 99), e['nama'], e.get('usia', 0), e.get('bup', 0), e.get('jabatan', '')[:40], a['skpd']))
    
    semua.sort(key=lambda x: x[0])
    for sisa, nama, usia, bup, jab, skpd in semua[:10]:
        icon = "🔴" if sisa <= 2 else "🟡" if sisa <= 5 else "🟢"
        print(f"  {icon} {nama:35s} | {usia:2d} thn | BUP {bup} thn | sisa {sisa:.1f} thn | {skpd}")

if __name__ == "__main__":
    hitung_semua()
