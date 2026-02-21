import sqlite3

def get_connection():
    return sqlite3.connect('storage.db')

# 1. Action: Save raw statement for the backend to see
def save_for_backend(user_id, file_name, text):
    db = get_connection()
    db.execute("INSERT INTO raw_statements (user_id, file_name, raw_text) VALUES (?, ?, ?)", 
               (user_id, file_name, text))
    db.commit()
    db.close()
    print("Uploaded to Backend Table.")

# 2. Action: User manually changes a category
def update_expense_manually(expense_id, new_category):
    db = get_connection()
    db.execute("UPDATE expenses SET category = ?, is_verified = 1 WHERE id = ?", 
               (new_category, expense_id))
    db.commit()
    db.close()
    print("Category updated manually.")

# TEST RUN
if __name__ == "__main__":
    print("Ready to process expenses...")