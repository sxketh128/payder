import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "payder.db")

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Reports from the community
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                reporter_wallet TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(identifier, reporter_wallet)
            )
        ''')
        
        # Log of agent checks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                status TEXT NOT NULL,
                check_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Log of x402 transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS x402_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                receipt TEXT NOT NULL,
                amount TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Local Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# DB Helpers
def add_report(identifier: str, reporter_wallet: str):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO reports (identifier, reporter_wallet) VALUES (?, ?)", 
                (identifier, reporter_wallet)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Already reported by this wallet

def count_reports(identifier: str) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reports WHERE identifier = ?", (identifier,))
        return cursor.fetchone()[0]

def log_check(identifier: str, status: str, check_type: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO checks (identifier, status, check_type) VALUES (?, ?, ?)", 
            (identifier, status, check_type)
        )
        conn.commit()

def log_x402_transaction(endpoint: str, receipt: str, amount: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO x402_transactions (endpoint, receipt, amount) VALUES (?, ?, ?)", 
            (endpoint, receipt, amount)
        )
        conn.commit()

def get_admin_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Recent checks
        cursor.execute("SELECT * FROM checks ORDER BY timestamp DESC LIMIT 5")
        recent_checks = [dict(row) for row in cursor.fetchall()]
        
        # Total flagged checks
        cursor.execute("SELECT COUNT(*) FROM checks WHERE status = 'Flagged'")
        flagged_count = cursor.fetchone()[0]
        
        # Total reports
        cursor.execute("SELECT COUNT(*) FROM reports")
        reports_count = cursor.fetchone()[0]
        
        # Total x402 txs
        cursor.execute("SELECT COUNT(*) FROM x402_transactions")
        x402_tx_count = cursor.fetchone()[0]
        
        return {
            "recent_checks": recent_checks,
            "flagged_count": flagged_count,
            "reports_count": reports_count,
            "x402_tx_count": x402_tx_count
        }

def create_user(email: str, password_hash: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)", 
                (email, password_hash)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def verify_user(email: str, password_hash: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?", (email, password_hash))
        return cursor.fetchone() is not None

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
