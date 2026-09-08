# database.py
import sqlite3
from datetime import datetime, timedelta

def init_db():
    """Luo tietokannan ja taulun, jos niitä ei ole olemassa."""
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS port_stats (
            timestamp DATETIME,
            total_ships INTEGER,
            total_oil REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_snapshot_if_needed(total_ships, total_oil):
    """Tallentaa uuden rivin tietokantaan enintään kerran tunnissa."""
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    
    c.execute('SELECT MAX(timestamp) FROM port_stats')
    last_timestamp = c.fetchone()[0]
    
    now = datetime.now()
    should_save = False
    
    if last_timestamp is None:
        should_save = True
    else:
        last_time = datetime.strptime(last_timestamp, '%Y-%m-%d %H:%M:%S')
        if now - last_time > timedelta(hours=1):
            should_save = True
            
    if should_save:
        c.execute('INSERT INTO port_stats (timestamp, total_ships, total_oil) VALUES (?, ?, ?)',
                  (now.strftime('%Y-%m-%d %H:%M:%S'), total_ships, total_oil))
        conn.commit()
    conn.close()

def get_historical_averages():
    """Hakee tietokannasta kaikkien aikojen keskiarvon (laivat ja öljy)."""
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute('SELECT AVG(total_ships), AVG(total_oil) FROM port_stats')
    result = c.fetchone()
    conn.close()
    
    avg_ships = result[0] if result[0] is not None else 0
    avg_oil = result[1] if result[1] is not None else 0
    
    return avg_ships, avg_oil

def get_total_db_rows():
 """Palauttaa tietokannan rivien kokonaismäärän."""
 conn = sqlite3.connect('history.db')
 c = conn.cursor()
 c.execute("SELECT COUNT(*) FROM port_stats")
 count = c.fetchone()[0]
 conn.close()
 return count
