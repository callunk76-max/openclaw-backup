
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
    cursor.execute("SELECT region_key FROM regions WHERE region_name LIKE '%Bulukumba%' OR display_name LIKE '%Bulukumba%'")
    res = cursor.fetchone()
    if not res:
        print("Error: Bulukumba region not found in regions table.")
        return
    
    bulukumba_key = res[0]
    print(f"Found region_key for Bulukumba: {bulukumba_key}")
    
    query = f"SELECT p.* FROM packages p JOIN package_regions pr ON p.id = pr.package_id WHERE pr.region_key = '{bulukumba_key}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    target_conn = sqlite3.connect(db_file)
    col_def = ", ".join([f'"{col}" TEXT' for col in columns])
    target_conn.execute(f"DROP TABLE IF EXISTS procurement")
    target_conn.execute(f"CREATE TABLE procurement ({col_def})")
    
    placeholders = ",".join(["?"] * len(columns))
    target_conn.executemany(f"INSERT INTO procurement VALUES ({placeholders})", rows)
    target_conn.commit()
    target_conn.close()
    conn.close()
    
    if os.path.exists('temp_nemesis_safe.db'):
        os.remove('temp_nemesis_safe.db')
        
    print(f"✅ Done! Imported {len(rows)} packages for Bulukumba into {db_file}")

if __name__ == "__main__":
    prepare_database()
