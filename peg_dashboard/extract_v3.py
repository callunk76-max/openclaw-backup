#!/usr/bin/env python3
"""Extract data from PDF laporan kinerja pegawai - v3 using table extraction."""
import os, re, json
import pdfplumber

DATA_DIR = "/root/.openclaw/workspace/peg_dashboard"
OUTPUT = os.path.join(DATA_DIR, "data.json")

def clean_agency_name(filename):
    """Extract readable agency name from filename."""
    name = filename.replace('.pdf', '').strip()
    name = re.sub(r'^(KINERJA\s+|LAPORAN\s+KINERJA\s+|LAPORAN\s+ABSEN\s+)', '', name)
    name = re.sub(r'\s+BULAN\s+SEPTEMBER\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+SEPT(?:EMBER)?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+SEPT\s*$', '', name, flags=re.IGNORECASE)
    name = name.strip()
    # Fix double spaces
    name = re.sub(r'\s+', ' ', name)
    return name

def parse_name_nip(cell):
    """Parse combined 'Name | NIP' cell."""
    if not cell:
        return "", ""
    parts = cell.split('|')
    name = parts[0].strip().rstrip(',').strip() if parts else ""
    nip = ""
    if len(parts) > 1:
        nip_match = re.search(r'\b(\d{15,18})\b', parts[1])
        if nip_match:
            nip = nip_match.group(1)
    # Also try finding NIP in name part
    if not nip:
        nip_match = re.search(r'\b(\d{15,18})\b', cell)
        if nip_match:
            nip = nip_match.group(1)
    # Clean name by removing NIP
    name = re.sub(r'\s*\d{15,18}\s*', '', name).strip()
    return name, nip

def determine_type(filename):
    f = filename.upper()
    if "ABSEN" in f:
        return "absensi"
    return "kinerja"

def extract_data():
    all_data = []
    
    for f in sorted(os.listdir(DATA_DIR)):
        if not f.endswith('.pdf'):
            continue
        
        filepath = os.path.join(DATA_DIR, f)
        print(f"[{f}]", end=" ", flush=True)
        
        try:
            agency = clean_agency_name(f)
            ftype = determine_type(f)
            employees = []
            seen_nips = set()
            
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if len(row) < 6:
                                continue
                            
                            # Check if first cell is a number (row number)
                            no_cell = (row[0] or "").strip()
                            if not re.match(r'^\d+$', no_cell):
                                continue  # skip header rows
                            
                            name_cell = row[1] or ""
                            golongan = (row[2] or "").strip()
                            jabatan = (row[3] or "").strip().replace('\n', ' ')
                            target_menit = (row[4] or "").strip()
                            capaian_menit = (row[5] or "").strip()
                            nilai_kinerja = ""
                            keterangan = ""
                            
                            if len(row) > 6:
                                nilai_kinerja = (row[6] or "").strip()
                            if len(row) > 7:
                                keterangan = (row[7] or "").strip()
                            
                            name, nip = parse_name_nip(name_cell)
                            
                            if nip and nip not in seen_nips:
                                seen_nips.add(nip)
                                
                                # Clean numeric fields
                                target_menit = re.sub(r'[^0-9]', '', target_menit)
                                capaian_menit = re.sub(r'[^0-9]', '', capaian_menit)
                                nilai_kinerja = re.sub(r'[^0-9.]', '', nilai_kinerja)
                                
                                # Skip empty entries
                                if not name and not nip:
                                    continue
                                
                                employees.append({
                                    "nama": name,
                                    "nip": nip,
                                    "golongan": golongan,
                                    "jabatan": jabatan,
                                    "target_menit": target_menit,
                                    "capaian_menit": capaian_menit,
                                    "nilai_kinerja": nilai_kinerja,
                                    "keterangan": keterangan
                                })
            
            # Clean jabatan - remove duplicate name at start
            for e in employees:
                j = e['jabatan']
                n = e['nama']
                if j.startswith(n[:20]):
                    e['jabatan'] = j[len(n):].strip().lstrip('|').strip()
                # Also clean if jabatan contains the NIP
                if e['nip'] in j:
                    e['jabatan'] = j.replace(e['nip'], '').strip().lstrip('|').strip()
            
            print(f"{len(employees)} pegawai")
            
            all_data.append({
                "file": f,
                "agency": agency,
                "type": ftype,
                "total_employees": len(employees),
                "employees": employees
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    # Save
    with open(OUTPUT, 'w') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total agencies: {len(all_data)}")
    total_emp = sum(a['total_employees'] for a in all_data)
    print(f"Total employees: {total_emp}")
    
    # Stats
    all_vals = []
    for a in all_data:
        for e in a['employees']:
            if e['nilai_kinerja']:
                try:
                    v = float(e['nilai_kinerja'])
                    if 0 < v <= 200:
                        all_vals.append(v)
                except:
                    pass
    
    if all_vals:
        print(f"Avg Kinerja: {sum(all_vals)/len(all_vals):.1f}%")
        print(f"Min: {min(all_vals):.1f}% | Max: {max(all_vals):.1f}%")
        print(f"Total with valid nilai: {len(all_vals)}")
    
    return all_data

if __name__ == "__main__":
    extract_data()
