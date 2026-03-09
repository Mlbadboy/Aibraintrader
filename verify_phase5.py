import requests
import sqlite3
import time
import os

DB_PATH = "app/feedback/feedback.db"
BASE_URL = "http://localhost:8000"

def test_phase5():
    print("--- Testing Phase 5: Self-Learning Feedback Loop ---")
    
    # Check if DB exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Make sure backend has started at least once.")
    
    # 1. Hit the endpoint
    print("\n[1] Triggering API to log a prediction (AAPL)...")
    res = requests.get(f"{BASE_URL}/analyze/stock/AAPL")
    
    if res.status_code != 200:
        print(f"API Failed: {res.text}")
        return
        
    print("API returned successfully. Data should be logged.")
    
    # Wait a tiny bit just in case (though it's synchronous)
    time.sleep(1)
    
    # 2. Check Database
    print("\n[2] Checking SQLite Database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            print("❌ No matching row found in the database.")
            return

        columns = [description[0] for description in cursor.description]
        data = dict(zip(columns, row))
        
        print("Found Latest Prediction Row:")
        for k, v in data.items():
            print(f"  {k}: {v}")
            
        if data['symbol'] == 'AAPL' and data['outcome'] == 'PENDING':
             print("\n✓ Feedback Loop Verification Successful")
        else:
             print("\n❌ Data mismatch in DB.")
             
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")

if __name__ == "__main__":
    test_phase5()
