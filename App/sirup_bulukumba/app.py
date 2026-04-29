from flask import Flask, render_template, request, send_file, jsonify
import sqlite3
import pandas as pd
import os
import json
import csv
import time
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)

VISITOR_PATH = '/root/.openclaw/workspace/App/sirup_bulukumba/visitor_count.json'
DB_PATH = '/root/.openclaw/workspace/App/sirup_bulukumba/bulukumba.db'

BUDGET_SQL = "CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)"
PER_PAGE = 50

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_visitor_count():
    try:
        with open(VISITOR_PATH, 'r') as f:
            data = json.load(f)
            return data.get('count', 0)
    except:
        return 0

def increment_visitor():
    count = get_visitor_count() + 1
    with open(VISITOR_PATH, 'w') as f:
        json.dump({'count': count}, f)
    return count

def get_last_update():
    try:
        mt = os.path.getmtime(DB_PATH)
        return time.strftime('%d.%m.%y||%H:%M', time.localtime(mt))
    except:
        return '--/--/--||--:--'

def parse_budget(budget_str):
    """Parse 'Rp 1,000,000' string to float"""
    if not budget_str:
        return 0
    return float(budget_str.replace('Rp ', '').replace(',', ''))

class FilterQuery:
    """Build and manage filter SQL queries"""
    def __init__(self, search_query='', m_filter='', type_filter=''):
        self.search_query = search_query
        self.m_filter = m_filter
        self.type_filter = type_filter

    def where_clause(self, alias='p'):
        """Build WHERE clause and return (clause_string, params_list)"""
        parts = []
        params = []
        prefix = f'{alias}.' if alias else ''

        if self.search_query:
            parts.append(f"({prefix}package_name LIKE ? OR {prefix}satker LIKE ?)")
            sq = f'%{self.search_query}%'
            params.extend([sq, sq])

        if self.m_filter:
            parts.append(f"{prefix}procurement_method = ?")
            params.append(self.m_filter)

        if self.type_filter:
            parts.append(f"{prefix}procurement_type = ?")
            params.append(self.type_filter)

        if parts:
            return ' AND '.join(parts), params
        return '', []

    @property
    def has_filters(self):
        return bool(self.search_query or self.m_filter or self.type_filter)


def get_threshold_case():
    """SQL CASE expression for PL threshold per procurement type"""
    return ("CASE WHEN procurement_type = 'Jasa Konsultansi' THEN 100000000 "
            "WHEN procurement_type = 'Pekerjaan Konstruksi' THEN 400000000 "
            "ELSE 200000000 END")


def fetch_table_data(conn, search_query, m_filter, type_filter, sort_by='id', sort_dir='DESC', page=1):
    """Fetch paginated table data + stats. Returns dict with all needed data."""
    fq = FilterQuery(search_query, m_filter, type_filter)
    offset = (page - 1) * PER_PAGE

    allowed_sorts = {
        'id': 'p.id',
        'package_name': 'p.package_name',
        'satker': 'p.satker',
        'budget': BUDGET_SQL
    }
    sort_col = allowed_sorts.get(sort_by, 'p.id')
    sort_dir_sql = 'ASC' if sort_dir.upper() == 'ASC' else 'DESC'

    # --- COUNT ---
    count_q = "SELECT COUNT(*) as cnt FROM procurement p"
    where_clause, params = fq.where_clause()
    if where_clause:
        count_q += f" WHERE {where_clause}"
    filtered_count = conn.execute(count_q, params).fetchone()['cnt'] or 0

    # --- DATA ---
    data_q = """SELECT p.*,
        COALESCE((
            SELECT SUM(r2."Total Nilai (Rp)") FROM realisasi r2
            WHERE r2."Kode RUP" = p.id
        ), (
            SELECT SUM(r3."Total Nilai (Rp)") FROM realisasi r3
            WHERE r3."Nama Paket" = p.package_name AND r3."Nama Satuan Kerja" = p.satker
        ), 0) as realisasi_total
    FROM procurement p"""
    if where_clause:
        data_q += f" WHERE {where_clause}"
    data_q += f" ORDER BY {sort_col} {sort_dir_sql} LIMIT {PER_PAGE} OFFSET {offset}"

    rows = conn.execute(data_q, params).fetchall()

    packages = []
    page_total_budget = 0
    for row in rows:
        pkg = dict(row)
        budget_num = parse_budget(pkg.get('budget'))
        pkg_real = pkg.get('realisasi_total', 0) or 0
        pkg['has_realisasi'] = pkg_real > 0
        pkg['realisasi_persen'] = round((pkg_real / budget_num) * 100, 1) if budget_num > 0 and pkg_real > 0 else 0
        # Determine PL over-limit for this package
        if pkg['procurement_method'] == 'Pengadaan Langsung':
            if pkg['procurement_type'] == 'Pekerjaan Konstruksi':
                pkg['_is_pl_over'] = budget_num > 400000000
            elif pkg['procurement_type'] == 'Jasa Konsultansi':
                pkg['_is_pl_over'] = budget_num > 100000000
            else:
                pkg['_is_pl_over'] = budget_num > 200000000
        else:
            pkg['_is_pl_over'] = False
        pkg['_row_num'] = offset + rows.index(row) + 1
        page_total_budget += budget_num
        packages.append(pkg)

    total_pages = max(1, (filtered_count + PER_PAGE - 1) // PER_PAGE)

    # --- FILTERED BUDGET ---
    fb_q = f"SELECT SUM({BUDGET_SQL}) FROM procurement p"
    if where_clause:
        fb_q += f" WHERE {where_clause}"
    filtered_total_budget = conn.execute(fb_q, params).fetchone()[0] or 0

    # --- FILTERED BREAKDOWN ---
    f_detail_q = f"""
        SELECT
            CASE WHEN procurement_method IN ('E-Purchasing', 'Pengadaan Langsung', 'Dikecualikan')
                 THEN procurement_method ELSE 'Lainnya' END as method_group,
            COUNT(*) as total, SUM({BUDGET_SQL}) as total_budget
        FROM procurement p
    """
    if where_clause:
        f_detail_q += f" WHERE {where_clause}"
    f_detail_q += " GROUP BY method_group"

    f_detail = conn.execute(f_detail_q, params).fetchall()
    fd = {'ep': 0, 'bd_ep': 0, 'pl': 0, 'bd_pl': 0, 'dk': 0, 'bd_dk': 0, 'ln': 0, 'bd_ln': 0}
    for row in f_detail:
        g, cnt, bgt = row['method_group'], row['total'], row['total_budget'] or 0
        if g == 'E-Purchasing': fd['ep'] = cnt; fd['bd_ep'] = bgt
        elif g == 'Pengadaan Langsung': fd['pl'] = cnt; fd['bd_pl'] = bgt
        elif g == 'Dikecualikan': fd['dk'] = cnt; fd['bd_dk'] = bgt
        else: fd['ln'] = cnt; fd['bd_ln'] = bgt

    return {
        'packages': packages,
        'filtered_count': filtered_count,
        'total_pages': total_pages,
        'current_page': page,
        'filtered_total_budget': filtered_total_budget,
        'page_total_budget': page_total_budget,
        **fd
    }


@app.route('/')
def index():
    total_visits = increment_visitor()
    last_update = get_last_update()

    search_query = request.args.get('search', '')
    m_filter = request.args.get('method', '')
    type_filter = request.args.get('type', '')
    sort_by = request.args.get('sort_by', 'id')
    sort_dir = request.args.get('sort_dir', 'DESC')
    page = int(request.args.get('page', 1))

    conn = get_db_connection()

    # Global stats (always the same, independent of filter)
    stats = conn.execute(
        f"SELECT COUNT(*) as total, SUM({BUDGET_SQL}) as total_budget FROM procurement"
    ).fetchone()

    detail_grouped = conn.execute(f"""
        SELECT
            CASE WHEN procurement_method IN ('E-Purchasing', 'Pengadaan Langsung', 'Dikecualikan')
                 THEN procurement_method ELSE 'Lainnya' END as method_group,
            COUNT(*) as total, SUM({BUDGET_SQL}) as total_budget
        FROM procurement GROUP BY method_group
    """).fetchall()

    total_epurchasing = 0; budget_epurchasing = 0
    total_pl = 0; budget_pl = 0
    total_dikecualikan = 0; budget_dikecualikan = 0
    total_lainnya = 0; budget_lainnya = 0
    for row in detail_grouped:
        g, cnt, bgt = row['method_group'], row['total'], row['total_budget'] or 0
        if g == 'E-Purchasing': total_epurchasing = cnt; budget_epurchasing = bgt
        elif g == 'Pengadaan Langsung': total_pl = cnt; budget_pl = bgt
        elif g == 'Dikecualikan': total_dikecualikan = cnt; budget_dikecualikan = bgt
        else: total_lainnya = cnt; budget_lainnya = bgt

    # Realisasi global
    real_total = conn.execute('SELECT SUM("Total Nilai (Rp)") FROM realisasi').fetchone()[0] or 0
    count_realized = conn.execute('SELECT COUNT(*) FROM realisasi').fetchone()[0] or 0

    real_grouped = conn.execute("""
        SELECT CASE WHEN "Metode Pengadaan" IN ('E-Purchasing', 'Pengadaan Langsung', 'Dikecualikan') THEN "Metode Pengadaan" ELSE 'Lainnya' END as method_group, SUM("Total Nilai (Rp)") as total_budget
        FROM realisasi GROUP BY method_group
    """).fetchall()
    real_epurchasing = 0; real_pl = 0; real_dikecualikan = 0; real_lainnya = 0
    for row in real_grouped:
        g, bgt = row['method_group'], row['total_budget'] or 0
        if g == 'E-Purchasing': real_epurchasing = bgt
        elif g == 'Pengadaan Langsung': real_pl = bgt
        elif g == 'Dikecualikan': real_dikecualikan = bgt
        else: real_lainnya = bgt

    # Table data (filtered/paginated)
    td = fetch_table_data(conn, search_query, m_filter, type_filter, sort_by, sort_dir, page)

    # Methods & types for filter dropdowns
    methods = conn.execute(
        "SELECT DISTINCT procurement_method FROM procurement WHERE procurement_method IS NOT NULL"
    ).fetchall()
    types = conn.execute(
        "SELECT DISTINCT procurement_type FROM procurement WHERE procurement_type IS NOT NULL"
    ).fetchall()

    # Suggestions
    suggestions = {
        "package_names": conn.execute("SELECT DISTINCT package_name FROM procurement").fetchall(),
        "satkers": conn.execute("SELECT DISTINCT satker FROM procurement").fetchall()
    }

    # Anomalies
    pl_anomaly_count = conn.execute(f"""
        SELECT COUNT(*) FROM procurement
        WHERE procurement_method = 'Pengadaan Langsung'
        AND {BUDGET_SQL} > {get_threshold_case()}
    """).fetchone()[0] or 0

    pl_anomalies = conn.execute(f"""
        SELECT id, package_name, satker, budget, procurement_type, work_description,
               'Pengadaan Langsung' as procurement_method,
               {get_threshold_case()} as threshold
        FROM procurement
        WHERE procurement_method = 'Pengadaan Langsung'
        AND {BUDGET_SQL} > {get_threshold_case()}
        ORDER BY {BUDGET_SQL} DESC
    """).fetchall()

    pagu_anomaly_count = conn.execute(f"""
        SELECT COUNT(*) FROM procurement p
        WHERE {BUDGET_SQL} > 0
        AND COALESCE(
            (SELECT SUM(r2."Total Nilai (Rp)") FROM realisasi r2 WHERE r2."Kode RUP" = p.id),
            (SELECT SUM(r3."Total Nilai (Rp)") FROM realisasi r3 WHERE r3."Nama Paket" = p.package_name AND r3."Nama Satuan Kerja" = p.satker), 0
        ) > {BUDGET_SQL}
    """).fetchone()[0] or 0

    pagu_anomalies = conn.execute(f"""
        SELECT p.id, p.package_name, p.satker, p.budget, p.procurement_method, p.procurement_type, p.work_description,
               COALESCE(
                   (SELECT SUM(r2."Total Nilai (Rp)") FROM realisasi r2 WHERE r2."Kode RUP" = p.id),
                   (SELECT SUM(r3."Total Nilai (Rp)") FROM realisasi r3 WHERE r3."Nama Paket" = p.package_name AND r3."Nama Satuan Kerja" = p.satker), 0
               ) as realisasi_total
        FROM procurement p
        WHERE {BUDGET_SQL} > 0
        AND COALESCE(
            (SELECT SUM(r2."Total Nilai (Rp)") FROM realisasi r2 WHERE r2."Kode RUP" = p.id),
            (SELECT SUM(r3."Total Nilai (Rp)") FROM realisasi r3 WHERE r3."Nama Paket" = p.package_name AND r3."Nama Satuan Kerja" = p.satker), 0
        ) > {BUDGET_SQL}
        ORDER BY realisasi_total DESC
    """).fetchall()

    conn.close()

    return render_template('index.html',
        # Global
        total_count=stats['total'],
        total_budget=stats['total_budget'],
        total_epurchasing=total_epurchasing, budget_epurchasing=budget_epurchasing,
        total_pl=total_pl, budget_pl=budget_pl,
        total_dikecualikan=total_dikecualikan, budget_dikecualikan=budget_dikecualikan,
        total_lainnya=total_lainnya, budget_lainnya=budget_lainnya,
        real_total=real_total, count_realized=count_realized,
        real_epurchasing=real_epurchasing, real_pl=real_pl,
        real_dikecualikan=real_dikecualikan, real_lainnya=real_lainnya,
        # Filtered
        packages=td['packages'],
        filtered_count=td['filtered_count'],
        total_pages=td['total_pages'],
        filtered_total_budget=td['filtered_total_budget'],
        page_total_budget=td['page_total_budget'],
        f_total_epurchasing=td['ep'], f_budget_epurchasing=td['bd_ep'],
        f_total_pl=td['pl'], f_budget_pl=td['bd_pl'],
        f_total_dikecualikan=td['dk'], f_budget_dikecualikan=td['bd_dk'],
        f_total_lainnya=td['ln'], f_budget_lainnya=td['bd_ln'],
        # Filters
        search_query=search_query, m_filter=m_filter, type_filter=type_filter,
        sort_by=sort_by, sort_dir=sort_dir, page=page, per_page=PER_PAGE,
        # UI data
        methods=methods, types=types, suggestions=suggestions,
        total_visits=total_visits, last_update=last_update,
        # Anomalies
        pl_anomalies=[dict(r) for r in pl_anomalies],
        pl_anomaly_count=pl_anomaly_count,
        pagu_anomalies=[dict(r) for r in pagu_anomalies],
        pagu_anomaly_count=pagu_anomaly_count
    )


@app.route('/api/table')
def api_table():
    """API endpoint returning JSON for AJAX table refresh."""
    search_query = request.args.get('search', '')
    m_filter = request.args.get('method', '')
    type_filter = request.args.get('type', '')
    sort_by = request.args.get('sort_by', 'id')
    sort_dir = request.args.get('sort_dir', 'DESC')
    page = int(request.args.get('page', 1))

    conn = get_db_connection()
    td = fetch_table_data(conn, search_query, m_filter, type_filter, sort_by, sort_dir, page)
    conn.close()

    return jsonify({
        'success': True,
        'packages': td['packages'],
        'filtered_count': td['filtered_count'],
        'total_pages': td['total_pages'],
        'current_page': td['current_page'],
        'filtered_total_budget': td['filtered_total_budget'],
        'page_total_budget': td['page_total_budget'],
        'f_total_epurchasing': td['ep'],
        'f_budget_epurchasing': td['bd_ep'],
        'f_total_pl': td['pl'],
        'f_budget_pl': td['bd_pl'],
        'f_total_dikecualikan': td['dk'],
        'f_budget_dikecualikan': td['bd_dk'],
        'f_total_lainnya': td['ln'],
        'f_budget_lainnya': td['bd_ln'],
    })


@app.route('/export')
def export():
    search_query = request.args.get('search', '')
    m_filter = request.args.get('method', '')
    type_filter = request.args.get('type', '')
    file_format = request.args.get('format', 'xlsx')

    conn = get_db_connection()
    fq = FilterQuery(search_query, m_filter, type_filter)
    query = "SELECT * FROM procurement WHERE 1=1"
    where_clause, params = fq.where_clause(alias='')
    if where_clause:
        query += f" AND {where_clause}"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    output = BytesIO()
    if file_format == 'xlsx':
        cols_to_export = ['id', 'package_name', 'satker', 'procurement_method', 'procurement_type', 'budget', 'work_description']
        df_export = df[cols_to_export].copy()
        df_export.columns = ['Kode RUP', 'Nama Paket', 'Satker', 'Metode', 'Tipe', 'Anggaran', 'Deskripsi']

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Data Pengadaan')
            worksheet = writer.sheets['Data Pengadaan']
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
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=20)
        elements.append(Paragraph("Laporan Data Pengadaan SIRUP Bulukumba", title_style))
        data = [['Kode RUP', 'Nama Paket', 'Satker', 'Metode', 'Anggaran']]
        df_pdf = df.head(500)
        for _, row in df_pdf.iterrows():
            pkg = Paragraph(str(row['package_name'])[:100] + ('...' if len(str(row['package_name']))>100 else ''), styles['Normal'])
            satker = Paragraph(str(row['satker'])[:80] + ('...' if len(str(row['satker']))>80 else ''), styles['Normal'])
            budget = str(row['budget'])
            data.append([str(row['id']), pkg, satker, str(row['procurement_method']), budget])
        table = Table(data, colWidths=[70, 250, 200, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        elements.append(table)
        if len(df) > 500:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                "* Catatan: Laporan PDF ini dibatasi 500 data pertama dari total {} data. "
                "Silakan gunakan filter atau unduh Excel untuk melihat selengkapnya.".format(len(df)),
                styles['Italic']))
        doc.build(elements)
        mime = 'application/pdf'
        filename = "sirup_bulukumba_export.pdf"
    else:
        df.to_csv(output, index=False, encoding='utf-8-sig')
        mime = 'text/csv'
        filename = "sirup_bulukumba_export.csv"

    output.seek(0)
    return send_file(output, mimetype=mime, as_attachment=True, download_name=filename)


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
            col_map = {
                'Kode RUP': 'id',
                'Nama Satuan Kerja': 'satker',
                'Nama Paket': 'package_name',
                'Metode Pengadaan': 'procurement_method',
                'Jenis Pengadaan': 'procurement_type',
                'Total Nilai (Rp)': 'budget',
                'Sumber Dana': 'funding_source',
                'Produk Dalam Negeri': 'is_umkm'
            }
            rename_dict = {k: v for k, v in col_map.items() if k in df_rup.columns}
            df_rup = df_rup.rename(columns=rename_dict)
            if 'work_description' not in df_rup.columns:
                df_rup['work_description'] = ''
            if 'risk_score' not in df_rup.columns:
                df_rup['risk_score'] = 0
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
        package_id = str(p_id) if p_id else ""
        query = 'SELECT * FROM realisasi WHERE "Kode RUP" = ?'
        realisasi = conn.execute(query, (package_id,)).fetchall()
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
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
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
                           vendors=vendors, total_count=total_count,
                           total_vendors=total_vendors, total_pt=total_pt,
                           total_perorangan=total_perorangan, total_lainnya=total_lainnya,
                           total_verified=total_verified,
                           search_query=search_query, verif_filter=verif_filter,
                           page=page, per_page=per_page)


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
        db_npwp_set = {}
        db_name_set = {}
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
            matched_id = None
            if file_npwp and file_npwp in db_npwp_set:
                matched_id = db_npwp_set[file_npwp]
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
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        conn.close()
    conn2 = get_db_connection()
    total_verified = conn2.execute('SELECT COUNT(*) FROM penyedia WHERE terverifikasi = 1').fetchone()[0]
    conn2.close()
    msg = f'✅ {marked} penyedia ditandai Terverifikasi!'
    if unmatched:
        msg += f'\n⚠️ {len(unmatched)} penyedia tidak ditemukan di database (periksa ejaan nama): {unmatched[:5]}{".." if len(unmatched) > 5 else ""}'
    return jsonify({'success': True, 'message': msg, 'total_verified': total_verified})


@app.route('/api/penyedia_detail')
def api_penyedia_detail():
    nama = request.args.get('nama', '').strip()
    if not nama:
        return jsonify({'success': False, 'message': 'Nama penyedia tidak diberikan'})
    conn = get_db_connection()
    try:
        # 1) Exact match
        row = conn.execute(
            'SELECT * FROM penyedia WHERE nama = ? LIMIT 1',
            (nama,)
        ).fetchone()
        if row:
            return jsonify({'success': True, 'data': dict(row)})

        # 2) LIKE partial match
        row = conn.execute(
            'SELECT * FROM penyedia WHERE nama LIKE ? LIMIT 1',
            (f'%{nama}%',)
        ).fetchone()
        if row:
            return jsonify({'success': True, 'data': dict(row)})

        # 3) Remove all spaces from both sides and compare (handles "GANES HA" vs "GANESHA")
        nama_nospace = nama.replace(' ', '')
        rows = conn.execute(
            "SELECT * FROM penyedia WHERE REPLACE(nama, ' ', '') = ? ORDER BY LENGTH(nama) ASC LIMIT 5",
            (nama_nospace,)
        ).fetchall()
        if rows:
            # Pick the one with shortest name (closest match to input)
            return jsonify({'success': True, 'data': dict(rows[0])})

        # 4) LIKE without spaces (partial) — rank by how close the name is
        rows = conn.execute(
            "SELECT * FROM penyedia WHERE REPLACE(nama, ' ', '') LIKE ? ORDER BY LENGTH(nama) ASC LIMIT 10",
            (f'%{nama_nospace}%',)
        ).fetchall()
        if rows:
            # Pick shortest name among results
            return jsonify({'success': True, 'data': dict(rows[0])})

        return jsonify({'success': False, 'message': 'Penyedia tidak ditemukan'})
    finally:
        conn.close()


@app.route('/penyedia/clear_verification', methods=['POST'])
def clear_verification():
    conn = get_db_connection()
    conn.execute('UPDATE penyedia SET terverifikasi = 0')
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Semua status verifikasi telah direset'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
