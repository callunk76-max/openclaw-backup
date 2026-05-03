
import sqlite3
import json
import os

def prepare_database():
    sql_file = '/root/.openclaw/workspace/nemesis_data.sql'
    db_file = '/root/.openclaw/workspace/App/sirup_bulukumba/bulukumba.db'
    
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found.")
        return

    print("Initializing SQLite database (Streaming Mode)...")
    temp_db = 'temp_nemesis.db'
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

    main_table = tables[0][0] 
    print(f"Processing table: {main_table} (JSON mode)...")
    
    target_conn = sqlite3.connect(db_//file) # Typos...
    # No, I'll just use the variable.
