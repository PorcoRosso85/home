#!/usr/bin/env bun

import Database from 'better-sqlite3';
import { resolve } from 'path';

// データベースファイルのパス
const DB_PATH = resolve(__dirname, '../litigation_risk.db');

// DDL: スキーマ定義とテーブル作成
function createSchema() {
  const db = new Database(DB_PATH);
  
  try {
    // 企業マスタテーブル
    db.exec(`
      CREATE TABLE IF NOT EXISTS companies (
        cik TEXT PRIMARY KEY,
        ticker TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // SEC提出書類テーブル
    db.exec(`
      CREATE TABLE IF NOT EXISTS filings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cik TEXT NOT NULL,
        form_type TEXT NOT NULL,
        filing_date DATE NOT NULL,
        accession_number TEXT NOT NULL,
        filing_url TEXT NOT NULL,
        risk_factors_text TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cik) REFERENCES companies(cik),
        UNIQUE(cik, accession_number)
      );
    `);

    // 訴訟パターンマスタテーブル
    db.exec(`
      CREATE TABLE IF NOT EXISTS litigation_patterns (
        pattern_id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        before_text TEXT,
        after_text TEXT,
        score INTEGER NOT NULL,
        precedent TEXT NOT NULL,
        outcome TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // パターンマッチング結果テーブル
    db.exec(`
      CREATE TABLE IF NOT EXISTS pattern_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filing_id INTEGER NOT NULL,
        pattern_id TEXT NOT NULL,
        match_score INTEGER NOT NULL,
        matched_text TEXT,
        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (filing_id) REFERENCES filings(id),
        FOREIGN KEY (pattern_id) REFERENCES litigation_patterns(pattern_id)
      );
    `);

    // アラート履歴テーブル
    db.exec(`
      CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER NOT NULL,
        alert_level TEXT NOT NULL CHECK(alert_level IN ('HIGH', 'MEDIUM', 'LOW')),
        message TEXT NOT NULL,
        notified BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES pattern_matches(id)
      );
    `);

    // インデックス作成
    db.exec(`
      CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik);
      CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);
      CREATE INDEX IF NOT EXISTS idx_matches_filing ON pattern_matches(filing_id);
      CREATE INDEX IF NOT EXISTS idx_matches_pattern ON pattern_matches(pattern_id);
      CREATE INDEX IF NOT EXISTS idx_alerts_match ON alerts(match_id);
      CREATE INDEX IF NOT EXISTS idx_alerts_notified ON alerts(notified);
    `);

    console.log('✅ スキーマ作成完了');
    console.log(`📁 データベース: ${DB_PATH}`);
    
    // テーブル一覧を表示
    const tables = db.prepare(`
      SELECT name FROM sqlite_master 
      WHERE type='table' 
      ORDER BY name
    `).all();
    
    console.log('\n📊 作成されたテーブル:');
    tables.forEach((table: any) => {
      console.log(`  - ${table.name}`);
    });

  } catch (error) {
    console.error('❌ スキーマ作成エラー:', error);
    process.exit(1);
  } finally {
    db.close();
  }
}

// 実行
if (import.meta.main) {
  createSchema();
}