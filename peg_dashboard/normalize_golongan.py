#!/usr/bin/env python3
"""Normalize golongan PNS ke format standar."""
import json, re

DATA_FILE = "/root/.openclaw/workspace/peg_dashboard/pegawai.json"

# Standar golongan PNS Indonesia
STANDAR_GOLONGAN = {
    "ia":  {"pangkat": "Juru Muda", "kode": "I/a", "index": 1},
    "ib":  {"pangkat": "Juru Muda Tingkat I", "kode": "I/b", "index": 2},
    "ic":  {"pangkat": "Juru", "kode": "I/c", "index": 3},
    "id":  {"pangkat": "Juru Tingkat I", "kode": "I/d", "index": 4},
    "iia": {"pangkat": "Pengatur Muda", "kode": "II/a", "index": 5},
    "iib": {"pangkat": "Pengatur Muda Tingkat I", "kode": "II/b", "index": 6},
    "iic": {"pangkat": "Pengatur", "kode": "II/c", "index": 7},
    "iid": {"pangkat": "Pengatur Tingkat I", "kode": "II/d", "index": 8},
    "iiia":{"pangkat": "Penata Muda", "kode": "III/a", "index": 9},
    "iiib":{"pangkat": "Penata Muda Tingkat I", "kode": "III/b", "index": 10},
    "iiic":{"pangkat": "Penata", "kode": "III/c", "index": 11},
    "iiid":{"pangkat": "Penata Tingkat I", "kode": "III/d", "index": 12},
    "iva": {"pangkat": "Pembina", "kode": "IV/a", "index": 13},
    "ivb": {"pangkat": "Pembina Tingkat I", "kode": "IV/b", "index": 14},
    "ivc": {"pangkat": "Pembina Muda", "kode": "IV/c", "index": 15},
    "ivd": {"pangkat": "Pembina Madya", "kode": "IV/d", "index": 16},
    "ive": {"pangkat": "Pembina Utama", "kode": "IV/e", "index": 17},
}

# Regex to extract golongan code - case insensitive
GOL_RE = re.compile(r'(IV[abcde]|III[a-d]|II[a-d]|I[a-d])', re.IGNORECASE)

def normalize_golongan(raw):
    """Parse raw golongan string and return standardized format."""
    if not raw or not raw.strip():
        return {"kode": "", "pangkat": "", "full": ""}
    
    clean = raw.replace('\n', '').strip()
    
    # Method 1: Extract golongan code from string like "Pembina Tingkat I/IVb"
    m = GOL_RE.search(clean)
    if m:
        code_raw = m.group(1).lower()
        if code_raw in STANDAR_GOLONGAN:
            std = STANDAR_GOLONGAN[code_raw]
            return {
                "kode": std["kode"],
                "pangkat": std["pangkat"],
                "full": f"{std['pangkat']} ({std['kode']})"
            }
    
    # Method 2: Fallback - infer from pangkat name (longest match first)
    mapping = [
        ("Penata Muda Tingkat I", "III/b", "Penata Muda Tingkat I"),
        ("Penata Muda", "III/a", "Penata Muda"),
        ("Penata Tingkat I", "III/d", "Penata Tingkat I"),
        ("Penata", "III/c", "Penata"),
        ("Pembina Utama Muda", "IV/c", "Pembina Muda"),
        ("Pembina Utama Madya", "IV/d", "Pembina Madya"),
        ("Pembina Utama", "IV/e", "Pembina Utama"),
        ("Pembina Tingkat I", "IV/b", "Pembina Tingkat I"),
        ("Pembina", "IV/a", "Pembina"),
        ("Pengatur Muda Tingkat I", "II/b", "Pengatur Muda Tingkat I"),
        ("Pengatur Muda", "II/a", "Pengatur Muda"),
        ("Pengatur Tingkat I", "II/d", "Pengatur Tingkat I"),
        ("Pengatur", "II/c", "Pengatur"),
        ("Juru Muda Tingkat I", "I/b", "Juru Muda Tingkat I"),
        ("Juru Muda", "I/a", "Juru Muda"),
        ("Juru Tingkat I", "I/d", "Juru Tingkat I"),
        ("Juru", "I/c", "Juru"),
    ]
    
    for nama_pangkat, gol_kode, pangkat_clean in mapping:
        if nama_pangkat.lower() in clean.lower():
            return {
                "kode": gol_kode,
                "pangkat": pangkat_clean,
                "full": f"{pangkat_clean} ({gol_kode})"
            }
    
    return {"kode": "", "pangkat": clean, "full": clean}

def main():
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    stats = {}
    fixes = []
    
    for a in data:
        for e in a['pegawai']:
            raw = e['golongan']
            normalized = normalize_golongan(raw)
            
            old_gol = e.get('golongan', '')
            e['golongan_kode'] = normalized['kode']
            e['golongan_pangkat'] = normalized['pangkat']
            e['golongan'] = normalized['full']
            
            if old_gol != normalized['full']:
                fixes.append((a['skpd'], e['nama'], old_gol, normalized['full']))
            
            k = normalized['kode']
            if k:
                stats[k] = stats.get(k, 0) + 1
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("=== DATA GOLONGAN SETELAH NORMALISASI ===")
    sorted_stats = sorted(stats.items(), key=lambda x: STANDAR_GOLONGAN.get(x[0].replace('/', ''), {"index": 99})["index"])
    for kode, count in sorted_stats:
        pangkat = STANDAR_GOLONGAN.get(kode.replace('/', '').lower(), {}).get('pangkat', '?')
        bar = '█' * (count // 10)
        print(f"  {kode:5s} | {pangkat:30s} | {count:4d} pegawai {bar}")
    
    unmapped = sum(1 for a in data for e in a['pegawai'] if not e['golongan_kode'])
    print(f"\n  ✅ Termapping: {sum(stats.values())}")
    print(f"  ❌ Tidak mapping: {unmapped}")
    print(f"  📊 Total: {sum(stats.values()) + unmapped}")
    
    if fixes:
        print(f"\nPerubahan ({len(fixes)}):")
        for skpd, nama, old, new in fixes[:10]:
            print(f"  {skpd:35s} | {nama:35s} | {old:35s} → {new}")

if __name__ == "__main__":
    main()
