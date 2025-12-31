import sqlite3
import csv

def create_emergency_data():
    # This creates a fresh database file named 'db_storage.db'
    conn = sqlite3.connect('db_storage.db')
    cursor = conn.cursor()
    
    # Create a table and add one row of data
    cursor.execute('CREATE TABLE IF NOT EXISTS test_table (id INTEGER, info TEXT)')
    cursor.execute('INSERT INTO test_table (id, info) VALUES (1, "Database is working!")')
    conn.commit()
    
    # Create the visible CSV preview
    cursor.execute('SELECT * FROM test_table')
    rows = cursor.fetchall()
    with open('visible_preview.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Information'])
        writer.writerows(rows)
    
    conn.close()
    print("Success! Created 'db_storage.db' and 'visible_preview.csv' in this folder.")

if __name__ == "__main__":
    create_emergency_data()