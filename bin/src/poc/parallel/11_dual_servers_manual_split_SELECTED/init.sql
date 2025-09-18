-- データベース初期化スクリプト
-- bin/docs規約準拠

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
  user_id VARCHAR(255) PRIMARY KEY,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- グローバル設定テーブル
CREATE TABLE IF NOT EXISTS global_settings (
  key VARCHAR(255) PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW(),
  synced BOOLEAN DEFAULT FALSE
);

-- 同期キューテーブル
CREATE TABLE IF NOT EXISTS sync_queue (
  id SERIAL PRIMARY KEY,
  path VARCHAR(255) NOT NULL,
  data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  processed BOOLEAN DEFAULT FALSE,
  processed_at TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_queue_processed ON sync_queue(processed);
CREATE INDEX IF NOT EXISTS idx_global_settings_updated_at ON global_settings(updated_at);