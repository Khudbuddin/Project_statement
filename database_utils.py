import sqlite3
import os

def get_db_connection(db_name):
    if not os.path.exists('databases'):
        os.makedirs('databases')
    
    db_path = os.path.join('databases', f"{db_name}.db")
    try:
        conn = sqlite3.connect(db_path)
        # This line helps you access columns by name later (e.g., user['email'])
        conn.row_factory = sqlite3.Row 
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

# CHECK THIS NAME CAREFULLY:
def create_table_if_not_exists(conn, table_sql):
    """Helper to create a table if it doesn't exist."""
    cursor = conn.cursor()
    try:
        cursor.execute(table_sql)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")