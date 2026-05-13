#!/usr/bin/env python3
"""Extract data kepegawaian from PDF Laporan Kinerja - only Nama, NIP, Gol, Jabatan"""
import os, re, json
import pdfplumber

DATA_DIR = "/root/.openclaw/workspace/peg_dashboard"
OUTPUT = os.path.join(DATA_DIR, "pegawai.json")

def clean_agency_name(filename):
    name = filename.replace('.pdf', '').strip()
    name = re.sub(r'^(KINERJA\s+|LAPORAN\s+KINERJA\s+|LAPORAN\s+ABSEN\s+)', '', name)
    name = re.sub(r'\s+BULAN\s+SEPTEMBER\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+SEPT(?:EMBER)?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+SEPT\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def parse_name_nip(cell):
    if not cell:
        return "", ""
    # NIP is 18 digit
    nip_match = re.search(r'\b(\d{18})\b', cell)
    nip = nip_match.group(1) if nip_match else ""
    # Name is everything before the NIP
    name = cell
    if nip:
        name = cell[:cell.index(nip)].strip().rstrip(',').strip()
    else:
        # Try 15-digit NIP
        nip_match2 = re.search(r'\b(\d{15})\b', cell)
        if nip_match2:
            nip = nip_match2.group(1)
            name = cell[:cell.index(nip)].strip().rstrip(',').strip()
    return name, nip

def extract_pegawai():
    all_skpd = []
    grand_total = 0

    for f in sorted(os.listdir(DATA_DIR)):
        if not f.endswith('.pdf'):
            continue
        
        filepath = os.path.join(DATA_DIR, f)
        print(f"[{f}]", end=" ", flush=True)
        
        try:
            agency = clean_agency_name(f)
            employees = []
            seen_nips = set()
            
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if len(row) < 4:
                                continue
                            # First cell should be row number
                            no_cell = (row[0] or "").strip()
                            if not re.match(r'^\d+$', no_cell):
                                continue
                            
                            name_cell = row[1] or ""
                            golongan = (row[2] or "").strip()
                            jabatan = (row[3] or "").strip().replace('\n', ' ')
                            
                            name, nip = parse_name_nip(name_cell)
                            
                            # Clean duplicate name in jabatan field
                            if nip and name and jabatan:
                                if name[:15].lower() in jabatan.lower():
                                    jabatan = ""
                            
                            if nip and nip not in seen_nips:
                                seen_nips.add(nip)
                                employees.append({
                                    "nama": name,
                                    "nip": nip,
                                    "golongan": golongan,
                                    "jabatan": jabatan[:100]  # trim long positions
                                })
            
            n = len(employees)
            grand_total += n
            print(f"{n} pegawai")
            
            all_skpd.append({
                "skpd": agency,
                "total": n,
                "pegawai": employees
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    with open(OUTPUT, 'w') as f:
        json.dump(all_skpd, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== RINGKASAN ===")
    print(f"Total SKPD: {len(all_skpd)}")
    print(f"Total pegawai: {grand_total}")
    print(f"File: {OUTPUT}")

if __name__ == "__main__":
    extract_pegawai()
