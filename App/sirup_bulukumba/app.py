
from flask import Flask, render_template, request, send_file, jsonify
import sqlite3
import pandas as pd
import os
import json
import csv
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)

DB_PATH = '/root/.openclaw/workspace/App/sirup_bulukumba/bulukumba.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    m_filter = request.args.get('method', '')
    type_filter = request.args.get('type', '')
    sort_by = request.args.get('sort_by', 'id')
    sort_dir = request.args.get('sort_dir', 'DESC')
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    # Validate sort_by to prevent SQL Injection
    allowed_sorts = {
        'id': 'id',
        'package_name': 'package_name',
        'satker': 'satker',
        'budget': 'CAST(REPLACE(REPLACE(budget, "Rp ", ""), ",", "") AS REAL)'
    }
    sort_column = allowed_sorts.get(sort_by, 'id')
    sort_direction = 'ASC' if sort_dir.upper() == 'ASC' else 'DESC'
    
    conn = get_db_connection()
    
    # Stats Global
    stats_query = "SELECT COUNT(*) as total, SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) as total_budget FROM procurement"
    stats = conn.execute(stats_query).fetchone()
    
    # Detail Global
    epurchasing_query = "SELECT COUNT(*) FROM procurement WHERE procurement_method = 'E-Purchasing'"
    total_epurchasing = conn.execute(epurchasing_query).fetchone()[0] or 0
    pengadaan_langsung_query = "SELECT COUNT(*) FROM procurement WHERE procurement_method = 'Pengadaan Langsung'"
    total_pl = conn.execute(pengadaan_langsung_query).fetchone()[0] or 0
    dikecualikan_query = "SELECT COUNT(*) FROM procurement WHERE procurement_method = 'Dikecualikan'"
    total_dikecualikan = conn.execute(dikecualikan_query).fetchone()[0] or 0
    lainnya_query = "SELECT COUNT(*) FROM procurement WHERE procurement_method NOT IN ('E-Purchasing', 'Pengadaan Langsung', 'Dikecualikan') OR procurement_method IS NULL"
    total_lainnya = conn.execute(lainnya_query).fetchone()[0] or 0
    
    epurchasing_budget_query = "SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE procurement_method = 'E-Purchasing'"
    budget_epurchasing = conn.execute(epurchasing_budget_query).fetchone()[0] or 0
    pengadaan_langsung_budget_query = "SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE procurement_method = 'Pengadaan Langsung'"
    budget_pl = conn.execute(pengadaan_langsung_budget_query).fetchone()[0] or 0
    dikecualikan_budget_query = "SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE procurement_method = 'Dikecualikan'"
    budget_dikecualikan = conn.execute(dikecualikan_budget_query).fetchone()[0] or 0
    lainnya_budget_query = "SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE procurement_method NOT IN ('E-Purchasing', 'Pengadaan Langsung', 'Dikecualikan') OR procurement_method IS NULL"
    budget_lainnya = conn.execute(lainnya_budget_query).fetchone()[0] or 0
    
    # Realisasi Global
    real_total = conn.execute('SELECT SUM("Total Nilai (Rp)") FROM realisasi').fetchone()[0] or 0
    count_realized = conn.execute('SELECT COUNT(*) FROM realisasi').fetchone()[0] or 0
    real_epurchasing = conn.execute('SELECT SUM("Total Nilai (Rp)") FROM realisasi WHERE "Metode Pengadaan" = \'E-Purchasing\'').fetchone()[0] or 0
    real_pl = conn.execute('SELECT SUM("Total Nilai (Rp)") FROM realisasi WHERE "Metode Pengadaan" = \'Pengadaan Langsung\'').fetchone()[0] or 0
    real_dikecualikan = conn.execute('SELECT SUM("Total Nilai (Rp)") FROM realisasi WHERE "Metode Pengadaan" = \'Dikecualikan\'').fetchone()[0] or 0
    real_lainnya = conn.execute('SELECT SUM("Total Nilai (Rp)") FROM realisasi WHERE ("Metode Pengadaan" NOT IN (\'E-Purchasing\', \'Pengadaan Langsung\', \'Dikecualikan\') OR "Metode Pengadaan" IS NULL)').fetchone()[0] or 0

    # Filter Logic
    query = """
    SELECT p.*, 
    EXISTS (
        SELECT 1 FROM realisasi r 
        WHERE r."Kode RUP" = p.id OR (r."Nama Paket" = p.package_name AND r."Nama Satuan Kerja" = p.satker)
    ) as has_realisasi
    FROM procurement p WHERE 1=1
    """
    params = []
    
    if search_query:
        query += " AND (package_name LIKE ? OR satker LIKE ? OR work_description LIKE ? OR id LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    
    if m_filter:
        query += " AND procurement_method = ?"
        params.append(m_filter)
        
    if type_filter:
        query += " AND procurement_type = ?"
        params.append(type_filter)
        
    # Corrected filtered query
    filtered_query = f"{query} ORDER BY {sort_column} {sort_direction}"
    total_filtered = conn.execute(filtered_query, params).fetchall()
    total_filtered_count = len(total_filtered)
    
    # Calculate Filtered Total Budget
    filtered_budget_query = "SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE 1=1"
    filtered_params = []
    if search_query:
        filtered_budget_query += " AND (package_name LIKE ? OR satker LIKE ? OR work_description LIKE ? OR id LIKE ?)"
        filtered_params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if m_filter:
        filtered_budget_query += " AND procurement_method = ?"
        filtered_params.append(m_filter)
    if type_filter:
        filtered_budget_query += " AND procurement_type = ?"
        filtered_params.append(type_filter)
        
    filtered_total_budget = conn.execute(filtered_budget_query, filtered_params).fetchone()[0] or 0
    
    # Detail Filtered
    filtered_epurchasing_query = f"SELECT COUNT(*) FROM procurement WHERE procurement_method = 'E-Purchasing'"
    filtered_epurchasing_budget_query = f"SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE procurement_method = 'E-Purchasing'"
    
    filtered_pl_query = f"SELECT COUNT(*) FROM procurement WHERE procurement_method = 'Pengadaan Langsung'"
    filtered_pl_budget_query = f"SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE procurement_method = 'Pengadaan Langsung'"
    
    filtered_dikecualikan_query = f"SELECT COUNT(*) FROM procurement WHERE procurement_method = 'Dikecualikan'"
    filtered_dikecualikan_budget_query = f"SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE procurement_method = 'Dikecualikan'"

    filtered_lainnya_query = "SELECT COUNT(*) FROM procurement WHERE (procurement_method NOT IN ('E-Purchasing', 'Pengadaan Langsung', 'Dikecualikan') OR procurement_method IS NULL)"
    filtered_lainnya_budget_query = "SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE (procurement_method NOT IN ('E-Purchasing', 'Pengadaan Langsung', 'Dikecualikan') OR procurement_method IS NULL)"
    
    # Append dynamic filter logic for detailed breakdown
    dynamic_condition = ""
    dynamic_params = []
    if search_query:
        dynamic_condition += " AND (package_name LIKE ? OR satker LIKE ? OR work_description LIKE ? OR id LIKE ?)"
        dynamic_params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if m_filter:
        dynamic_condition += " AND procurement_method = ?"
        dynamic_params.append(m_filter)
    if type_filter:
        dynamic_condition += " AND procurement_type = ?"
        dynamic_params.append(type_filter)
        
    f_total_epurchasing = conn.execute(filtered_epurchasing_query + dynamic_condition, dynamic_params).fetchone()[0] or 0
    f_budget_epurchasing = conn.execute(filtered_epurchasing_budget_query + dynamic_condition, dynamic_params).fetchone()[0] or 0
    
    f_total_pl = conn.execute(filtered_pl_query + dynamic_condition, dynamic_params).fetchone()[0] or 0
    f_budget_pl = conn.execute(filtered_pl_budget_query + dynamic_condition, dynamic_params).fetchone()[0] or 0
    
    f_total_dikecualikan = conn.execute(filtered_dikecualikan_query + dynamic_condition, dynamic_params).fetchone()[0] or 0
    f_budget_dikecualikan = conn.execute(filtered_dikecualikan_budget_query + dynamic_condition, dynamic_params).fetchone()[0] or 0

    f_total_lainnya = conn.execute(filtered_lainnya_query + dynamic_condition, dynamic_params).fetchone()[0] or 0
    f_budget_lainnya = conn.execute(filtered_lainnya_budget_query + dynamic_condition, dynamic_params).fetchone()[0] or 0
    
    # Pagination
    total_pages = (total_filtered_count + per_page - 1) // per_page
    paginated_query = f"{filtered_query} LIMIT {per_page} OFFSET {offset}"
    rows = conn.execute(paginated_query, params).fetchall()
    
    # Convert sqlite3.Row to dict for JSON serialization in template
    packages = [dict(row) for row in rows]
    
    # Calculate Page Total Budget
    page_budget_query = f"SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM ({paginated_query})"
    page_total_budget = conn.execute(page_budget_query, params).fetchone()[0] or 0
    
    # Suggestions
    suggestions = {
        "package_names": conn.execute("SELECT DISTINCT package_name FROM procurement").fetchall(),
        "satkers": conn.execute("SELECT DISTINCT satker FROM procurement").fetchall()
    }
    
    methods = conn.execute("SELECT DISTINCT procurement_method FROM procurement WHERE procurement_method IS NOT NULL").fetchall()
    types = conn.execute("SELECT DISTINCT procurement_type FROM procurement WHERE procurement_type IS NOT NULL").fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                           packages=packages, 
                           total_count=stats['total'], 
                           filtered_count=total_filtered_count,
                           total_pages=total_pages,
                           total_budget=stats['total_budget'],
                           filtered_total_budget=filtered_total_budget,
                           page_total_budget=page_total_budget,
                           methods=methods,
                           types=types,
                           search_query=search_query,
                           m_filter=m_filter,
                           type_filter=type_filter,
                           sort_by=sort_by,
                           sort_dir=sort_dir,
                           page=page,
                           per_page=per_page,
                           suggestions=suggestions,
                           # Stats Global Details
                           total_epurchasing=total_epurchasing,
                           total_pl=total_pl,
                           total_dikecualikan=total_dikecualikan,
                           total_lainnya=total_lainnya,
                           budget_epurchasing=budget_epurchasing,
                           budget_pl=budget_pl,
                           budget_dikecualikan=budget_dikecualikan,
                           budget_lainnya=budget_lainnya,
                           real_total=real_total,
                           count_realized=count_realized,
                           real_epurchasing=real_epurchasing,
                           real_pl=real_pl,
                           real_dikecualikan=real_dikecualikan,
                           real_lainnya=real_lainnya,
                           # Stats Filtered Details
                           f_total_epurchasing=f_total_epurchasing,
                           f_total_pl=f_total_pl,
                           f_total_dikecualikan=f_total_dikecualikan,
                           f_total_lainnya=f_total_lainnya,
                           f_budget_epurchasing=f_budget_epurchasing,
                           f_budget_pl=f_budget_pl,
                           f_budget_dikecualikan=f_budget_dikecualikan,
                           f_budget_lainnya=f_budget_lainnya
                           )

@app.route('/export')
def export():
    search_query = request.args.get('search', '')
    m_filter = request.args.get('method', '')
    type_filter = request.args.get('type', '')
    file_format = request.args.get('format', 'xlsx')
    
    conn = get_db_connection()
    query = "SELECT * FROM procurement WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (package_name LIKE ? OR satker LIKE ? OR work_description LIKE ? OR id LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    
    if m_filter:
        query += " AND procurement_method = ?"
        params.append(m_filter)
        
    if type_filter:
        query += " AND procurement_type = ?"
        params.append(type_filter)
        
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    output = BytesIO()
    if file_format == 'xlsx':
        # Select and rename columns for Excel to make it beautiful
        cols_to_export = ['id', 'package_name', 'satker', 'procurement_method', 'procurement_type', 'budget', 'work_description']
        df_export = df[cols_to_export].copy()
        df_export.columns = ['Kode RUP', 'Nama Paket', 'Satker', 'Metode', 'Tipe', 'Anggaran', 'Deskripsi']
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Data Pengadaan')
            worksheet = writer.sheets['Data Pengadaan']
            # Auto-adjust column widths roughly
            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 40)
            worksheet.set_column('C:C', 35)
            worksheet.set_column('D:E', 15)
            worksheet.set_column('F:F', 20)
            worksheet.set_column('G:G', 50)
            
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = "sirup_bulukumba_export.xlsx"
        
    elif file_format == 'pdf':
        doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=20)
        elements.append(Paragraph("Laporan Data Pengadaan SIRUP Bulukumba", title_style))
        
        # Data prep
        data = [['Kode RUP', 'Nama Paket', 'Satker', 'Metode', 'Anggaran']]
        
        # Limit PDF export to 500 rows to prevent memory/timeout issues
        df_pdf = df.head(500)
        
        for _, row in df_pdf.iterrows():
            # Wrap text to prevent bleeding out of cells
            pkg = Paragraph(str(row['package_name'])[:100] + ('...' if len(str(row['package_name']))>100 else ''), styles['Normal'])
            satker = Paragraph(str(row['satker'])[:80] + ('...' if len(str(row['satker']))>80 else ''), styles['Normal'])
            budget = str(row['budget'])
            data.append([str(row['id']), pkg, satker, str(row['procurement_method']), budget])
            
        # Create table with col widths
        table = Table(data, colWidths=[70, 250, 200, 100, 100])
        
        # Style the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ])
        table.setStyle(style)
        
        elements.append(table)
        
        if len(df) > 500:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"* Catatan: Laporan PDF ini dibatasi 500 data pertama dari total {len(df)} data untuk menjaga performa. Silakan gunakan filter atau unduh Excel untuk melihat selengkapnya.", styles['Italic']))
            
        doc.build(elements)
        mime = 'application/pdf'
        filename = "sirup_bulukumba_export.pdf"
        
    else:
        # Fallback csv
        df.to_csv(output, index=False, encoding='utf-8-sig')
        mime = 'text/csv'
        filename = "sirup_bulukumba_export.csv"
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype=mime,
        as_attachment=True,
        download_name=filename
    )

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    password = request.form.get('password')
    if password != 'Callunk13':
        return jsonify({'success': False, 'message': 'Password salah!'}), 403
        
    rup_file = request.files.get('rup_file')
    realisasi_file = request.files.get('realisasi_file')
    
    if (not rup_file or rup_file.filename == '') and (not realisasi_file or realisasi_file.filename == ''):
        return jsonify({'success': False, 'message': 'Minimal satu file harus diupload!'}), 400
        
    try:
        conn = sqlite3.connect(DB_PATH)
        
        if rup_file and rup_file.filename != '':
            df_rup = pd.read_csv(rup_file, low_memory=False)
            
            # Map raw CSV columns to expected DB columns
            col_map = {
                'Kode RUP': 'id',
                'Nama Satuan Kerja': 'satker',
                'Nama Paket': 'package_name',
                'Metode Pengadaan': 'procurement_method',
                'Jenis Pengadaan': 'procurement_type',
                'Total Nilai (Rp)': 'budget',
                'Sumber Dana': 'funding_source',
                'Produk Dalam Negeri': 'is_umkm' # Using as proxy for simplicity
            }
            rename_dict = {k: v for k, v in col_map.items() if k in df_rup.columns}
            df_rup = df_rup.rename(columns=rename_dict)
            
            # Ensure required columns exist to prevent 500 errors
            if 'work_description' not in df_rup.columns:
                df_rup['work_description'] = ''
            if 'risk_score' not in df_rup.columns:
                df_rup['risk_score'] = 0
                
            # Format budget to match old string format (e.g. "Rp 1,000,000") if it's numeric
            if 'budget' in df_rup.columns and pd.api.types.is_numeric_dtype(df_rup['budget']):
                df_rup['budget'] = df_rup['budget'].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "Rp 0")
            
            df_rup.to_sql('procurement', conn, if_exists='replace', index=False)
            
        if realisasi_file and realisasi_file.filename != '':
            df_realisasi = pd.read_csv(realisasi_file, low_memory=False)
            df_realisasi.to_sql('realisasi', conn, if_exists='replace', index=False)
            
        conn.close()
        
        return jsonify({'success': True, 'message': 'Database berhasil diupdate!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/package_details')
def package_details():
    package_name = request.args.get('package_name', '')
    satker = request.args.get('satker', '')
    p_id = request.args.get('id', '')
    
    conn = get_db_connection()
    try:
        # Strict mapping: first try to match exactly by Kode RUP
        package_id = str(p_id) if p_id else ""
        
        query = 'SELECT * FROM realisasi WHERE "Kode RUP" = ?'
        realisasi = conn.execute(query, (package_id,)).fetchall()
        
        # Fallback for empty Kode RUP cases or when RUP ID changed but it's the exact same package.
        # But to be safe from duplicate mismatched sums, we only fallback if there's no match by ID yet,
        # AND we try to find a match by exact Name and Satker.
        if len(realisasi) == 0:
            query_fb = 'SELECT * FROM realisasi WHERE "Nama Paket" = ? AND "Nama Satuan Kerja" = ?'
            realisasi = conn.execute(query_fb, (package_name, satker)).fetchall()
            
        result = [dict(row) for row in realisasi]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/penyedia/export')
def export_penyedia():
    search_query = request.args.get('search', '')
    verif_filter = request.args.get('verif', '')
    file_format = request.args.get('format', 'xlsx')
    
    conn = get_db_connection()
    
    query = "SELECT nama, npwp, email, tanggal_daftar, jenis_usaha, alamat, telepon, terverifikasi FROM penyedia WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (nama LIKE ? OR npwp LIKE ? OR jenis_usaha LIKE ? OR alamat LIKE ?)"
        sq = f'%{search_query}%'
        params.extend([sq, sq, sq, sq])
    
    if verif_filter == 'verified':
        query += " AND terverifikasi = 1"
    elif verif_filter == 'unverified':
        query += " AND (terverifikasi IS NULL OR terverifikasi = 0)"
    elif verif_filter == 'pt':
        query += " AND jenis_usaha LIKE '%PT%'"
    elif verif_filter == 'perorangan':
        query += " AND (jenis_usaha LIKE '%Perorangan%' OR jenis_usaha LIKE '%Usaha Perorangan%')"
    
    query += " ORDER BY nama ASC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    output = BytesIO()
    
    if file_format == 'xlsx':
        df_export = df.copy()
        df_export.columns = ['Nama Penyedia', 'NPWP', 'Email', 'Tanggal Daftar', 'Jenis Usaha', 'Alamat', 'Telepon', 'Terverifikasi']
        df_export['Terverifikasi'] = df_export['Terverifikasi'].apply(lambda x: '✅ Ya' if x == 1 else '⬜ Belum')
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Penyedia')
            worksheet = writer.sheets['Penyedia']
            worksheet.set_column('A:A', 35)
            worksheet.set_column('B:B', 22)
            worksheet.set_column('C:C', 30)
            worksheet.set_column('D:D', 18)
            worksheet.set_column('E:E', 22)
            worksheet.set_column('F:F', 45)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 14)
            
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = 'penyedia_bulukumba.xlsx'
        
    elif file_format == 'pdf':
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=20, textColor=colors.HexColor('#059669'))
        elements.append(Paragraph('Daftar Penyedia Terverifikasi Kab. Bulukumba', title_style))
        
        data = [['No', 'Nama Penyedia', 'NPWP', 'Jenis Usaha', 'Status']]
        
        df_pdf = df.head(1000)
        for idx, (_, row) in enumerate(df_pdf.iterrows(), 1):
            status = '✅ Terverifikasi' if row['terverifikasi'] == 1 else '⬜ Belum'
            nama = Paragraph(str(row['nama'])[:60], styles['Normal'])
            data.append([str(idx), nama, str(row['npwp']), str(row['jenis_usaha']), status])
        
        table = Table(data, colWidths=[30, 280, 160, 120, 80])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
        ])
        table.setStyle(style)
        elements.append(table)
        
        if len(df) > 1000:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f'* Menampilkan 1000 data pertama dari total {len(df)} data.', styles['Italic']))
        
        doc.build(elements)
        mime = 'application/pdf'
        filename = 'penyedia_bulukumba.pdf'
    else:
        df.to_csv(output, index=False, encoding='utf-8-sig')
        mime = 'text/csv'
        filename = 'penyedia_bulukumba.csv'
    
    output.seek(0)
    return send_file(output, mimetype=mime, as_attachment=True, download_name=filename)

@app.route('/penyedia')
def list_penyedia():
    search_query = request.args.get('search', '')
    verif_filter = request.args.get('verif', '')
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    
    count_query = "SELECT COUNT(*) FROM penyedia WHERE 1=1"
    data_query = "SELECT * FROM penyedia WHERE 1=1"
    params = []
    
    if search_query:
        count_query += " AND (nama LIKE ? OR npwp LIKE ? OR jenis_usaha LIKE ? OR alamat LIKE ?)"
        data_query += " AND (nama LIKE ? OR npwp LIKE ? OR jenis_usaha LIKE ? OR alamat LIKE ?)"
        sq = f'%{search_query}%'
        params.extend([sq, sq, sq, sq])
    
    if verif_filter == 'verified':
        count_query += " AND terverifikasi = 1"
        data_query += " AND terverifikasi = 1"
    elif verif_filter == 'unverified':
        count_query += " AND (terverifikasi IS NULL OR terverifikasi = 0)"
        data_query += " AND (terverifikasi IS NULL OR terverifikasi = 0)"
    elif verif_filter == 'pt':
        count_query += " AND jenis_usaha LIKE '%PT%'"
        data_query += " AND jenis_usaha LIKE '%PT%'"
    elif verif_filter == 'perorangan':
        count_query += " AND (jenis_usaha LIKE '%Perorangan%' OR jenis_usaha LIKE '%Usaha Perorangan%')"
        data_query += " AND (jenis_usaha LIKE '%Perorangan%' OR jenis_usaha LIKE '%Usaha Perorangan%')"
    
    total_count = conn.execute(count_query, params).fetchone()[0] or 0
    
    data_query += " ORDER BY nama ASC LIMIT ? OFFSET ?"
    data_params = params + [per_page, offset]
    
    vendors = conn.execute(data_query, data_params).fetchall()
    
    total_vendors = conn.execute("SELECT COUNT(*) FROM penyedia").fetchone()[0] or 0
    total_pt = conn.execute("SELECT COUNT(*) FROM penyedia WHERE jenis_usaha LIKE '%PT%'").fetchone()[0] or 0
    total_perorangan = conn.execute("SELECT COUNT(*) FROM penyedia WHERE jenis_usaha LIKE '%Perorangan%'").fetchone()[0] or 0
    total_lainnya = total_vendors - total_pt - total_perorangan
    total_verified = conn.execute("SELECT COUNT(*) FROM penyedia WHERE terverifikasi = 1").fetchone()[0] or 0
    
    conn.close()
    
    return render_template('penyedia.html',
                           vendors=vendors,
                           total_count=total_count,
                           total_vendors=total_vendors,
                           total_pt=total_pt,
                           total_perorangan=total_perorangan,
                           total_lainnya=total_lainnya,
                           total_verified=total_verified,
                           search_query=search_query,
                           verif_filter=verif_filter,
                           page=page,
                           per_page=per_page)

@app.route('/penyedia/upload', methods=['POST'])
def upload_penyedia():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang diupload'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nama file kosong'})
    
    conn = get_db_connection()
    marked = 0
    errors = []
    
    try:
        all_npwp_normalized = []
        all_names = []
        
        if file.filename.endswith('.csv'):
            import io
            content = file.read().decode('utf-8')
            import csv
            first_line = content.split('\n')[0].strip().lower()
            has_headers = any(kw in first_line for kw in ['npwp', 'nama', 'penyedia', 'email', 'tanggal'])
            
            if has_headers:
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    npwp = (row.get('NPWP', '') or '').strip()
                    nama = (row.get('Nama Penyedia', row.get('Nama', '')) or '').strip()
                    if npwp or nama:
                        all_npwp_normalized.append(npwp.replace('.','').replace('-','').replace(' ',''))
                        all_names.append(nama.upper().strip())
            else:
                reader = csv.reader(io.StringIO(content))
                for row in reader:
                    if len(row) >= 2:
                        nama = (row[0] or '').strip()
                        npwp = (row[1] or '').strip()
                        all_npwp_normalized.append(npwp.replace('.','').replace('-','').replace(' ',''))
                        all_names.append(nama.upper().strip())
                        
        elif file.filename.endswith(('.xlsx', '.xls')):
            import openpyxl
            import io
            wb = openpyxl.load_workbook(io.BytesIO(file.read()), data_only=True)
            ws = wb.active
            
            first_row_values = [str(ws.cell(1, c).value or '').strip().lower() for c in range(1, min(ws.max_column + 1, 10))]
            has_headers = any(kw in ','.join(first_row_values) for kw in ['npwp', 'nama', 'penyedia', 'email', 'tanggal', 'usaha'])
            
            if has_headers:
                headers = first_row_values
                npwp_col = next((c for c, h in enumerate(headers) if 'npwp' in h), None)
                nama_col = next((c for c, h in enumerate(headers) if 'nama' in h or 'penyedia' in h), None)
                start_row = 2
            else:
                npwp_col = 1
                nama_col = 0
                start_row = 1
            
            for row in range(start_row, ws.max_row + 1):
                npwp = str(ws.cell(row, (npwp_col or 0) + 1).value or '').strip() if npwp_col is not None else ''
                nama = str(ws.cell(row, (nama_col or 0) + 1).value or '').strip() if nama_col is not None else ''
                if npwp or nama:
                    all_npwp_normalized.append(npwp.replace('.','').replace('-','').replace(' ',''))
                    all_names.append(nama.upper().strip())
        else:
            return jsonify({'success': False, 'message': 'Format file tidak didukung. Gunakan .csv, .xlsx, atau .xls'})
        
        # Now match against database
        # Build lookup sets for fast matching
        db_npwp_set = {}  # normalized_npwp -> id
        db_name_set = {}  # uppercased_name -> id
        
        all_db = conn.execute('SELECT id, nama, npwp, terverifikasi FROM penyedia').fetchall()
        for v in all_db:
            nn = (v['npwp'] or '').replace('.','').replace('-','').replace(' ','').strip()
            nm = (v['nama'] or '').upper().strip()
            if nn: db_npwp_set[nn] = v['id']
            if nm: db_name_set[nm] = v['id']
        
        marked = 0
        matched_ids = set()
        unmatched = []
        
        for i in range(len(all_npwp_normalized)):
            file_npwp = all_npwp_normalized[i]
            file_nama = all_names[i]
            
            if not file_nama:
                continue
                
            # Try match by NPWP first
            matched_id = None
            if file_npwp and file_npwp in db_npwp_set:
                matched_id = db_npwp_set[file_npwp]
            # Fallback: match by name
            elif file_nama in db_name_set:
                matched_id = db_name_set[file_nama]
            
            if matched_id:
                if matched_id not in matched_ids:
                    conn.execute('UPDATE penyedia SET terverifikasi = 1 WHERE id = ?', (matched_id,))
                    matched_ids.add(matched_id)
                    marked += 1
            else:
                unmatched.append(file_nama.title())
        
        conn.commit()
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        conn.close()
    
    # Count total verified
    conn2 = get_db_connection()
    total_verified = conn2.execute('SELECT COUNT(*) FROM penyedia WHERE terverifikasi = 1').fetchone()[0]
    conn2.close()
    
    msg = f'✅ {marked} penyedia ditandai Terverifikasi!'
    if unmatched:
        msg += f'\n⚠️ {len(unmatched)} penyedia tidak ditemukan di database (periksa ejaan nama): {unmatched[:5]}{".." if len(unmatched) > 5 else ""}'
    
    return jsonify({'success': True, 'message': msg, 'total_verified': total_verified})

@app.route('/penyedia/clear_verification', methods=['POST'])
def clear_verification():
    conn = get_db_connection()
    conn.execute('UPDATE penyedia SET terverifikasi = 0')
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Semua status verifikasi telah direset'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)

