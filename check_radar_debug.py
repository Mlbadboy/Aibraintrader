import sqlite3
import os

def check_radar():
    db_path = "app/radar/radar.db"
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        # Try finding it relative to script
        alt_path = os.path.join(os.path.dirname(__file__), "app", "radar", "radar.db")
        if os.path.exists(alt_path):
            db_path = alt_path
            print(f"Found DB at {db_path}")
        else:
            print("Could not find database anywhere.")
            return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Watchlist ---")
    cursor.execute("SELECT * FROM watchlist")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- Radar Results ---")
    cursor.execute("SELECT * FROM radar_results")
    rows = cursor.fetchall()
    if not rows:
        print("No results found in radar_results table.")
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_radar()
