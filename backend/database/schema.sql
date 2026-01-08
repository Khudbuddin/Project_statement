-- 1. User Info Storage
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT, 
    auth_provider TEXT DEFAULT 'local'
);

-- 2. Bank Statements Storage (Raw Data)
CREATE TABLE IF NOT EXISTS bank_statements (
    stmt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    description TEXT,
    amount REAL,
    ml_category TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- 3. Manual Changes Storage (Safe for ML)
CREATE TABLE IF NOT EXISTS manual_adjustments (
    adj_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stmt_id INTEGER,
    new_category TEXT,
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stmt_id) REFERENCES bank_statements (stmt_id)
);