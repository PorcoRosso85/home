#!/usr/bin/env python3
"""
DDL: risk.db のスキーマ定義（TSLA専用MVP）
"""

import sqlite3
from pathlib import Path

# データベースパス
DB_PATH = Path(__file__).parent.parent / "risk.db"

def create_schema():
    """TSLAのリスク分析用の最小限のテーブルを作成"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 企業テーブル（TSLAのみハードコード）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            cik TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
    
    # TSLAをハードコードで挿入
    cursor.execute("""
        INSERT OR IGNORE INTO companies (cik, ticker, name)
        VALUES ('0001318605', 'TSLA', 'Tesla, Inc.')
    """)
    
    # 2. 10-K提出書類テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cik TEXT NOT NULL,
            filing_date DATE NOT NULL,
            accession_number TEXT NOT NULL,
            risk_factors_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. パターンマッチング結果テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pattern_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id INTEGER NOT NULL,
            pattern_name TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            precedent TEXT,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (filing_id) REFERENCES filings(id)
        )
    """)
    
    # 4. アラートテーブル（最終的な警告）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            message TEXT NOT NULL,
            severity INTEGER NOT NULL,  -- 87 = 87%一致など
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ データベース作成完了: {DB_PATH}")
    print("📊 作成されたテーブル:")
    print("  - companies (TSLA固定)")
    print("  - filings (10-K保存用)")
    print("  - pattern_matches (マッチング結果)")
    print("  - alerts (最終警告)")

if __name__ == "__main__":
    create_schema()