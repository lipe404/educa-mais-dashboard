import sqlite3
import pandas as pd
import os

db_path = r"c:\Users\toled\Documents\GitHub\educa-mais-dashboard\auto-comissao\instance\commission_system.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", tables)
        
        # Select from partners
        try:
            df = pd.read_sql_query("SELECT * FROM partners", conn)
            print("\nPartners Data:")
            print(df.head())
        except Exception as e:
            print(f"Error reading partners: {e}")
            
        conn.close()
    except Exception as e:
        print(f"Error connecting: {e}")
