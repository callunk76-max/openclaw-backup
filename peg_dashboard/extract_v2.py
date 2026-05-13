#!/usr/bin/env python3
"""Extract data from PDF laporan kinerja pegawai using pdfplumber."""
import os, re, json, sys
import pdfplumber

DATA_DIR = "/root/.openclaw/workspace/peg_dashboard"
OUTPUT = os.path.join(DATA_DIR, "data.json")

def extract_tables_from_pdf(filepath):
    """Extract text content and tables from a PDF."""
    results = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            # Try table extraction
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    cleaned = [c.strip() if c else "" for c in row]
                    results.append(cleaned)
    
    return results

def clean_agency_name(filename):
    """Extract readable agency name from filename."""
    name = filename.replace('.pdf', '').strip()
    name = re.sub(r'^(KINERJA\s+|LAPORAN\s+KINERJA\s+LAPORAN\s+ABSEN\s+)', '', name)
    name = re.sub(r'\s+BULAN\s+SEPTEMBER\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+SEPT(?:EMBER)?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+SEPT\s*$', '', name, flags=re.IGNORECASE)
    return name.strip()

def is_name_with_nip(lines, start_idx):
    """Check if lines starting at start_idx contain a name with NIP."""
    if start_idx >= len(lines):
        return False
    combined = " ".join(lines[start_idx:start_idx+3])
    return bool(re.search(r'\d{15,18}', combined))

def extract_data():
    """Extract employee data from all PDFs."""
    all_data = []
    
    for f in sorted(os.listdir(DATA_DIR)):
        if not f.endswith('.pdf'):
            continue
        
        filepath = os.path.join(DATA_DIR, f)
        print(f"[{f}] Processing...", end=" ", flush=True)
        
        try:
            tables = extract_tables_from_pdf(filepath)
            agency = clean_agency_name(f)
            
            # Try to determine the type
            ftype = "kinerja"
            if "ABSEN" in f.upper():
                ftype = "absensi"
            
            # Extract employees from table data
            employees = []
            seen_nips = set()
            
            for row in tables:
                if len(row) < 3:
                    continue
                
                # Try to find NIP in any cell
                nip = None
                name = ""
                for cell in row:
                    m = re.search(r'\b(\d{15,18})\b', cell)
                    if m:
                        nip = m.group(1)
                        # Name is usually before NIP in the cell
                        name_part = cell[:cell.index(nip)].strip().rstrip(',').strip()
                        name = name_part
                        break
                
                if nip and nip not in seen_nips:
                    seen_nips.add(nip)
                    
                    golongan = ""
                    jabatan = ""
                    target_menit = ""
                    capaian_menit = ""
                    nilai_kinerja = ""
                    
                    # Parse remaining cells for golongan, jabatan, metrics
                    for cell in row:
                        cell_clean = cell.strip()
                        # Check for golongan patterns
                        gol_patterns = ['Pembina', 'Penata', 'Pengatur', 'Juru']
                        for gp in gol_patterns:
                            if gp in cell_clean and not golongan:
                                golongan = cell_clean
                        
                        # Check for jabatan patterns
                        jab_patterns = ['Kepala', 'Sekretaris', 'Bidang', 'Sub', 'JF ', 'PLT', 'Staf', 'Bendahara', 'Pelaksana']
                        for jp in jab_patterns:
                            if cell_clean.startswith(jp) and not jabatan:
                                jabatan = cell_clean
                        
                        # Check for numeric values (target, capaian, nilai)
                        if re.match(r'^\d{4,5}$', cell_clean):
                            if not target_menit:
                                target_menit = cell_clean
                            elif not capaian_menit:
                                capaian_menit = cell_clean
                        
                        if re.match(r'^\d{1,3}(\.\d)?$', cell_clean) and not nilai_kinerja:
                            # 1-3 digit number, possible percentage
                            val = float(cell_clean)
                            if 0 <= val <= 200:
                                nilai_kinerja = cell_clean
                    
                    employees.append({
                        "nama": name,
                        "nip": nip,
                        "golongan": golongan,
                        "jabatan": jabatan,
                        "target_menit": target_menit,
                        "capaian_menit": capaian_menit,
                        "nilai_kinerja": nilai_kinerja
                    })
            
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
            import traceback
            traceback.print_exc()
    
    # Save
    with open(OUTPUT, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total agencies: {len(all_data)}")
    total_emp = sum(a['total_employees'] for a in all_data)
    print(f"Total employees: {total_emp}")
    
    # Quick stats
    all_emps = []
    for a in all_data:
        for e in a['employees']:
            if e['nilai_kinerja']:
                all_emps.append(e)
    
    if all_emps:
        vals = [float(e['nilai_kinerja']) for e in all_emps if e['nilai_kinerja']]
        if vals:
            print(f"Avg Kinerja: {sum(vals)/len(vals):.1f}%")
            print(f"Min: {min(vals):.1f}% | Max: {max(vals):.1f}%")
    
    return all_data

if __name__ == "__main__":
    extract_data()
