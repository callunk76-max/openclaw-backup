#!/usr/bin/env python3
"""Tambahkan kolom Tgl Lahir, Jenis Kelamin, TMT dari NIP."""
import json

DATA_FILE = "/root/.openclaw/workspace/peg_dashboard/pegawai.json"

def parse_nip(nip):
    """Parse 18-digit NIP and return extra info."""
    if len(nip) != 18 or not nip.isdigit():
        return None
    
    yyyy = nip[:4]
    mm = nip[4:6]
    dd = nip[6:8]
    
    # Tanggal Lahir
    tgl_lahir = f"{yyyy}-{mm}-{dd}"
    
    # TMT (digit 9-14: YYYYMM)
    tmt_yyyy = nip[8:12]
    tmt_mm = nip[12:14]
    tmt = f"{tmt_yyyy}-{tmt_mm}"
    
    # Jenis Kelamin (digit 15: 1=Pria, 2=Wanita)
    jk_digit = nip[14:15]
    if jk_digit == '1':
        jenis_kelamin = "L"
    elif jk_digit == '2':
        jenis_kelamin = "P"
    else:
        jenis_kelamin = "?"
    
    return {
        "tgl_lahir": tgl_lahir,
        "tmt": tmt,
        "jenis_kelamin": jenis_kelamin,
        "jk_digit": jk_digit
    }

def main():
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    stats = {"laki": 0, "perempuan": 0, "unknown": 0, "invalid": 0}
    
    for a in data:
        for e in a['pegawai']:
            nip = e.get('nip', '')
            info = parse_nip(nip)
            
            if info:
                e['tgl_lahir'] = info['tgl_lahir']
                e['tmt'] = info['tmt']
                e['jenis_kelamin'] = info['jenis_kelamin']
                
                if info["jenis_kelamin"] == "L":
                    stats['l'] += 1
                elif info["jenis_kelamin"] == "P":
                    stats['p'] += 1
                else:
                    stats['unk'] += 1
            else:
                e['tgl_lahir'] = ""
                e['tmt'] = ""
                e['jenis_kelamin'] = ""
                stats['invalid'] += 1
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    total = sum(stats.values())
    print("=== DATA KEPEGAWAIAN DIPERKAYA ===")
    print(f"  ✅ Total:    {total}")
    print(f"  👨 Laki-laki:  {{stats['l'] ({stats['l']/total*100:.1f}%)")
    print(f"  👩 Perempuan:  {stats['p']} ({stats['p']/total*100:.1f}%)")
    print(f"  ❌ Invalid:    {stats['invalid']}")
    
    # Sample
    for a in data:
        e = a['pegawai'][0]
        if e.get('tgl_lahir'):
            print(f"\nContoh: {e['nama']}")
            print(f"  NIP: {e['nip']}")
            print(f"  Lahir: {e['tgl_lahir']}")
            print(f"  JK: {e['jenis_kelamin']}")
            print(f"  TMT: {e['tmt']}")
            break

if __name__ == "__main__":
    main()
