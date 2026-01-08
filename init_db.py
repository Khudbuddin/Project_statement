import sqlite3
import os

DB_NAME = "smart_expense.db"
SCHEMA_PATH = os.path.join("backend", "database", "schema.sql")

def get_db_connection():
    """Ye function backend/frontend se connect karne mein kaam aayega"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Isse data dictionary format mein milta hai (Easy for Frontend)
    return conn

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r") as f:
            cursor.executescript(f.read())
        conn.commit()
        print("✅ Database & 3 Storage Tables Ready!")
    else:
        print(f"❌ Error: {SCHEMA_PATH} nahi mila!")
        return

    # TEST DATA (Optional)
    try:
        cursor.execute("INSERT OR IGNORE INTO users (name, email, auth_provider) VALUES (?, ?, ?)", 
                       ("Project Partner", "team@example.com", "local"))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Test Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()