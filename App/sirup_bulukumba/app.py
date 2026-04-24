
from flask import Flask, render_template, request, send_file
import sqlite3
import pandas as pd
import os
from io import BytesIO

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
        'budget': 'CAST(REPLACE(REPLACE(budget, "Rp ", ""), ",", "") AS REAL)',
        'risk_score': 'CAST(risk_score AS REAL)'
    }
    sort_column = allowed_sorts.get(sort_by, 'id')
    sort_direction = 'ASC' if sort_dir.upper() == 'ASC' else 'DESC'
    
    conn = get_db_connection()
    
    # Stats
    stats_query = "SELECT COUNT(*) as total, SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) as total_budget FROM procurement"
    stats = conn.execute(stats_query).fetchone()
    
    # Filter Logic
    query = "SELECT * FROM procurement WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (package_name LIKE ? OR satker LIKE ? OR work_description LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    
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
    filtered_budget_query = f"SELECT SUM(CAST(REPLACE(REPLACE(budget, 'Rp ', ''), ',', '') AS REAL)) FROM procurement WHERE 1=1"
    filtered_params = []
    if search_query:
        filtered_budget_query += " AND (package_name LIKE ? OR satker LIKE ? OR work_description LIKE ?)"
        filtered_params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if m_filter:
        filtered_budget_query += " AND procurement_method = ?"
        filtered_params.append(m_filter)
    if type_filter:
        filtered_budget_query += " AND procurement_type = ?"
        filtered_params.append(type_filter)
        
    filtered_total_budget = conn.execute(filtered_budget_query, filtered_params).fetchone()[0] or 0
    
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
                           suggestions=suggestions)

@app.route('/export')
def export():
    search_query = request.args.get('search', '')
    m_filter = request.args.get('method', '')
    type_filter = request.args.get('type', '')
    file_format = request.args.get('format', 'csv')
    
    conn = get_db_connection()
    query = "SELECT * FROM procurement WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (package_name LIKE ? OR satker LIKE ? OR work_description LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    
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
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
    else:
        df.to_csv(output, index=False, encoding='utf-8-sig')
    
    output.seek(0)
    
    mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_format == 'xlsx' else 'text/csv'
    filename = f"sirup_bulukumba_{file_format}.{file_format}"
    
    return send_file(
        output,
        mimetype=mime,
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
