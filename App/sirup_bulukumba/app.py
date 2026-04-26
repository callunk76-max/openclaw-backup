
from flask import Flask, render_template, request, send_file, jsonify
import sqlite3
import pandas as pd
import os
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
