from database_utils import get_db_connection, create_table_if_not_exists
import bcrypt

# --- SCHEMAS ---
USER_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    google_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

BANK_TABLE = """
CREATE TABLE IF NOT EXISTS bank_statements (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_name TEXT,
    file_path TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

OVERRIDE_TABLE = """
CREATE TABLE IF NOT EXISTS user_overrides (
    override_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    transaction_id_ref TEXT UNIQUE, 
    manual_category TEXT,
    user_notes TEXT,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

def initialize_all_dbs():
    dbs = {
        "auth_storage": USER_TABLE,
        "bank_data": BANK_TABLE,
        "overrides": OVERRIDE_TABLE
    }
    for db_name, schema in dbs.items():
        conn = get_db_connection(db_name)
        create_table_if_not_exists(conn, schema)
        conn.close()
    print("✅ All databases initialized.")

if __name__ == "__main__":
    initialize_all_dbs()