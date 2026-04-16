import sqlite3

db_path = 'data/pallavi.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table list
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'[DB] Tables: {tables}')
    
    # Check tickets table schema
    if 'tickets' in tables:
        cursor.execute("PRAGMA table_info(tickets)")
        cols = cursor.fetchall()
        print('\n[SCHEMA] Tickets columns:')
        for col in cols:
            print(f'  {col[1]} - {col[2]}')
        
        # Get recent records
        cursor.execute('SELECT * FROM tickets ORDER BY rowid DESC LIMIT 5')
        rows = cursor.fetchall()
        print(f'\n[DATA] Recent {len(rows)} tickets:')
        for row in rows:
            print(f'  {row}')
    else:
        print('[WARNING] No tickets table found')
    
    conn.close()
except Exception as e:
    print(f'[ERROR] {e}')
