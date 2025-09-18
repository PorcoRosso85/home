import sqlite3
import json
from datetime import datetime
from pathlib import Path


class EmailDB:
    def __init__(self, db_path="emails.db"):
        self.db_path = Path(db_path)
        self.init_db()
    
    def init_db(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    subject TEXT,
                    sender TEXT,
                    recipient TEXT,
                    body TEXT,
                    timestamp DATETIME,
                    raw_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider ON emails(provider);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON emails(timestamp);
            """)
    
    def store_email(self, email_id, provider, subject, sender, recipient, body, timestamp, raw_data=None):
        """メールをデータベースに保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO emails 
                (id, provider, subject, sender, recipient, body, timestamp, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (email_id, provider, subject, sender, recipient, body, timestamp, 
                  json.dumps(raw_data) if raw_data else None))
    
    def get_emails(self, provider=None, limit=100):
        """メールを取得"""
        with sqlite3.connect(self.db_path) as conn:
            if provider:
                cursor = conn.execute("""
                    SELECT * FROM emails WHERE provider = ? 
                    ORDER BY timestamp DESC LIMIT ?
                """, (provider, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM emails 
                    ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
            return cursor.fetchall()
    
    def email_exists(self, email_id):
        """メールIDが既に存在するかチェック"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM emails WHERE id = ?", (email_id,))
            return cursor.fetchone() is not None