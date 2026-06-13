import sqlite3
from pathlib import Path

def get_connection():
    # This finds the 'storage.db' in the main project folder
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    db_path = BASE_DIR / "storage.db"
    return sqlite3.connect(str(db_path))

# --- 1. AUTHENTICATION (Crucial for Frontend) ---
def verify_user(email, password):
    db = get_connection()
    cursor = db.cursor()
    # Check TIER 1 table
    cursor.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    db.close()
    return user # Returns (id, email) if found, else None

def create_user(email, password):
    try:
        db = get_connection()
        db.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        db.commit()
        db.close()
        return True
    except:
        return False

# --- 2. BACKEND ACTIONS (Your Colleague's Code) ---
def save_for_backend(user_id, file_name, text):
    db = get_connection()
    db.execute("INSERT INTO raw_statements (user_id, file_name, raw_text) VALUES (?, ?, ?)", 
               (user_id, file_name, text))
    db.commit()
    db.close()
    print("Uploaded to Backend Table.")

def update_expense_manually(expense_id, new_category):
    db = get_connection()
    db.execute("UPDATE expenses SET category = ?, is_verified = 1 WHERE id = ?", 
               (new_category, expense_id))
    db.commit()
    db.close()
    print("Category updated manually.")

if __name__ == "__main__":
    print("Ready to process expenses...")