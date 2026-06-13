import sqlite3

def create_tables():
    # This creates the 'storage.db' file automatically
    connection = sqlite3.connect('storage.db')
    cursor = connection.cursor()

    # TIER 1: User Info (Gmail/Passwords)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT,
            is_google_user BOOLEAN DEFAULT 0
        )
    ''')

    # TIER 2: Raw Bank Statements (For Backend/AI processing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_name TEXT,
            raw_text TEXT,
            processed_status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # TIER 3: Editable Expenses (Manual changes allowed here)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            description TEXT,
            is_verified BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    connection.commit()
    connection.close()
    print("✅ Database and 3 Tables are ready!")

if __name__ == "__main__":
    create_tables()