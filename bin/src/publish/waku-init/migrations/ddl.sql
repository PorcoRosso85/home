-- Waku-Init Forms Database Schema
-- 汎用フォーム送信データ管理用テーブル

-- フォーム送信データテーブル
CREATE TABLE IF NOT EXISTS form_submissions (
  -- 主キー
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  
  -- 必須基本フィールド
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  
  -- 柔軟なデータ格納（JSON形式）
  data JSON DEFAULT '{}',  -- 追加フィールド用（message, phone, company, etc.）
  
  -- ファイル参照（R2オブジェクトキーの配列）
  files JSON DEFAULT '[]',  -- ["uploads/2024/file1.pdf", "uploads/2024/file2.jpg"]
  
  -- メタデータ
  form_type TEXT,           -- 'contact', 'survey', 'feedback', etc.
  status TEXT DEFAULT 'pending', -- 'pending', 'processed', 'archived'
  ip_address TEXT,
  user_agent TEXT,
  
  -- タイムスタンプ
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- パフォーマンス向上のためのインデックス
CREATE INDEX IF NOT EXISTS idx_form_email ON form_submissions(email);
CREATE INDEX IF NOT EXISTS idx_form_type ON form_submissions(form_type);
CREATE INDEX IF NOT EXISTS idx_form_status ON form_submissions(status);
CREATE INDEX IF NOT EXISTS idx_form_created ON form_submissions(created_at DESC);

-- JSONフィールド検索用の仮想カラムインデックス（オプション）
-- CREATE INDEX idx_form_data_message ON form_submissions(json_extract(data, '$.message'));

-- サンプルデータ（開発用）
/*
INSERT INTO form_submissions (name, email, data, form_type) VALUES 
  ('テストユーザー', 'test@example.com', '{"message":"テストメッセージ"}', 'contact'),
  ('サンプル太郎', 'sample@example.com', '{"company":"株式会社サンプル", "phone":"090-1234-5678"}', 'contact');
*/