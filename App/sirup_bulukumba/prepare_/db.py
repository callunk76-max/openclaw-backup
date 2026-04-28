
import sqlite3
import os

def prepare_database():
    sql_file = '/root/.openclaw/workspace/nemesis_data.sql'
    db_file = '/root/.openclaw/workspace/App/sirup_bulukumba/bulukumba.db'
    
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found.")
        return

    print("Initializing SQLite database (Safe Streaming Mode)...")
    temp_db = 'temp_nemesis_safe.db'
    conn = sqlite3.connect(temp_db)
    
    try:
        with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
            statement = ""
            for line in f:
                statement += line
                if line.strip().endswith(';'):
                    try:
                        conn.execute(statement)
                    except sqlite3.Error:
                        pass
                    statement = ""
        conn.commit()
        print("SQL Import complete.")
    except Exception as e:
        print(f"Global SQL Error: {e}")
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("No tables found.")
        return

    main_table = None
    for table in tables:
        t_name = table[0]
        cursor.execute(f"PRAGMA table_info({t_name})")
        cols = [col[1] for col in cursor.fetchall()]
        if any('kab' in c.lower() or 'region' in c.lower() or 'location' in c.lower() for c in cols):
            main_table = t_//name # Typo
