#!/usr/bin/env python3
"""Extract data from PDF laporan kinerja pegawai Bulukumba."""
import os, re, json
from pdfminer.high_level import extract_text

DATA_DIR = "/root/.openclaw/workspace/peg_dashboard"
OUTPUT = os.path.join(DATA_DIR, "data.json")

def parse_nipnip(line):
    """Try to extract NIP from a line containing numbers."""
    m = re.search(r'\b(\d{18}|\d{15,16})\b', line)
    return m.group(1) if m else None

def extract_performance(text, filename):
    """Extract employee performance data from a PDF text dump."""
    lines = text.split('\n')
    
    # Determine agency name - usually the 3rd or 4th line
    agency = filename.replace('.pdf', '')
    agency = re.sub(r'^(KINERJA\s+|LAPORAN\s+KINERJA\s+|LAPORAN\s+ABSEN\s+)', '', agency)
    agency = agency.strip()
    
    # We know the table columns from header analysis:
    # No | Nama / NIP | Pangkat Golongan | Nama Jabatan | Target | Capaian Menit | Nilai Kinerja | Keterangan
    
    # Strategy: extract lines that are numeric percentages (Nilai Kinerja)
    # then work backwards to get the employee info
    
    employees = []
    current = {}
    buffer_positions = []  # track where position names end
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and header lines
        if not line or line in ('No', '', 'Rekap', 'REKAPITULASI', 'CAPAIAN', 'PRODUKTIFITAS', 'KERJA',
                                '(AKTIVITAS)', 'BULAN', 'SEPTEMBER'):
            i += 1
            continue
        
        # Look for lines that are just numbers (the right-side columns)
        # Nilai Kinerja typically 0-100 or 100+
        # Target/Capaian are 4-5 digit numbers
        
        i += 1
    
    return {"agency": agency, "employees": employees}

def extract_all():
    """Extract data from all PDF files."""
    all_data = []
    
    for f in sorted(os.listdir(DATA_DIR)):
        if not f.endswith('.pdf'):
            continue
        
        filepath = os.path.join(DATA_DIR, f)
        print(f"Processing: {f}...", end=" ")
        
        text = extract_text(filepath)
        lines = text.split('\n')
        
        # Clean lines
        lines = [l.strip() for l in lines if l.strip()]
        
        # Determine agency name from filename
        basename = f.replace('.pdf', '')
        agency_name = basename
        
        # Detect type from filename
        ftype = "kinerja"
        if basename.upper().startswith("LAPORAN ABSEN") or basename.upper().startswith("LAPORAN KINERJA"):
            ftype = "kinerja"
        
        # Extract employees using pattern matching
        # Pattern: Name NIP ... golongan ... jabatan ... target ... capaian ... nilai%
        employees = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip header lines
            skip_words = ['REKAPITULASI', 'CAPAIAN', 'PRODUKTIFITAS', 'KERJA', '(AKTIVITAS)',
                         'BULAN', 'SEPTEMBER', 'No', 'Nama', 'NIP', 'Pangkat', 'Golongan',
                         'Jabatan', 'Target', 'Menit', 'Setelah', 'Penyesuai', 'an', 'Hari',
                         'Libur', 'Capaian', 'Nilai', 'Kinerja', 'setelah', 'penyesuaian',
                         'Keterangan', 'hari', 'libur', '(%)', 'PEMERINTAH', 'KABUPATEN',
                         'BULUKUMBA', 'Andi', 'Penata', 'Pembina', 'Pengatur', 'Juru',
                         'Pelaksana', 'Kepala', 'Sekretaris', 'Bidang', 'Sub', 'JF',
                         'PLT', 'Staf', 'Bendahara', 'Analis', 'Pengelola', 'Pengolah']
            
            # Check if line looks like a number entry (simplified)
            # The actual data entries are letters/names, not just headers
            
            # Better approach: find numeric rows that represent metrics
            if re.match(r'^\d+$', line) and len(line) >= 3 and len(line) <= 6:
                # Could be a metric value (target/capaian/nilai)
                pass
            
            i += 1
        
        # Alternative approach: use the raw text and regex patterns
        # The PDF has structure: Name rows interspersed with numbers
        
        # Let's find all NIP patterns (18 digit or 15-16 digit)
        nip_pattern = re.findall(r'\b(\d{18}|\d{15,16})\b', text)
        
        # Get all lines
        all_lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Find positions of NIPs in the line list
        nip_positions = []
        for idx, l in enumerate(all_lines):
            if re.match(r'^\d{15,18}$', l):
                nip_positions.append(idx)
        
        print(f"Found {len(nip_positions)} employees")
        
        # Extract employee info
        for pos_idx, nip_idx in enumerate(nip_positions):
            name_line = all_lines[nip_idx - 1] if nip_idx > 0 else ""
            nip = all_lines[nip_idx]
            
            # Find golongan (search backward from nip_idx)
            golongan = ""
            jabatan = ""
            target_val = ""
            capaian_val = ""
            nilai_val = ""
            
            # Look for golongan pattern (IVe, IVd, IVc, IVb, IVa, IIId, IIIc, IIIb, IIIa, IId, IIc, IIb, IIa, Id, Ic, Ib, Ia)
            golongan_patterns = ['Pembina Utama Madya', 'Pembina Utama Muda', 'Pembina Tingkat I',
                                'Pembina', 'Penata Tingkat I', 'Penata Muda Tingkat I', 
                                'Penata', 'Penata Muda', 'Pengatur Tingkat I', 
                                'Pengatur', 'Pengatur Muda Tingkat I', 'Pengatur Muda',
                                'Juru Tingkat I', 'Juru', 'Juru Muda Tingkat I', 'Juru Muda']
            
            for lookback in range(1, 6):
                if nip_idx >= lookback:
                    prev = all_lines[nip_idx - lookback]
                    for gp in golongan_patterns:
                        if gp in prev or gp.upper() in prev.upper():
                            golongan = all_lines[nip_idx - lookback]
                            break
                if golongan:
                    break
            
            # Find jabatan (lines between golongan and name, or around it)
            # Find target/capaian/nilai forward from nip_idx
            for lookahead in range(1, 8):
                if nip_idx + lookahead < len(all_lines):
                    next_line = all_lines[nip_idx + lookahead]
                    # Target values are typically 4-digit numbers (7800, 8400, etc.)
                    if re.match(r'^\d{4}$', next_line):
                        if not target_val:
                            target_val = next_line
                        elif not capaian_val:
                            capaian_val = next_line
                        elif not nilai_val:
                            nilai_val = next_line
                            break
            
            # Clean name
            name = name_line.strip(', ')
            
            employees.append({
                "nama": name,
                "nip": nip,
                "golongan": golongan,
                "jabatan": jabatan,
                "target_menit": target_val,
                "capaian_menit": capaian_val,
                "nilai_kinerja": nilai_val
            })
        
        entry = {
            "file": basename,
            "agency": agency_name,
            "type": ftype,
            "total_employees": len(employees),
            "employees": employees
        }
        all_data.append(entry)
        print(f"Done - {len(employees)} pegawai")
    
    # Save
    with open(OUTPUT, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\nData saved to {OUTPUT}")
    print(f"Total agencies: {len(all_data)}")
    print(f"Total employees: {sum(a['total_employees'] for a in all_data)}")

if __name__ == "__main__":
    extract_all()
