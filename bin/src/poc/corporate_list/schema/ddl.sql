-- ========================================
-- 企業リード収集システム SQLite DDL
-- ========================================
-- 設計方針:
-- 1. 企業名は正規化してcompaniesテーブルで管理
-- 2. 記事データは別テーブルで履歴追跡
-- 3. KuzuDB連携用のrelテーブルを用意
-- ========================================

-- 企業マスタ（正規化）
CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,           -- 正式企業名
  normalized_name TEXT,                 -- 表記ゆれ統一用（カタカナ、小文字等）
  aliases TEXT,                         -- 別名リスト（JSON配列）
  industry TEXT,                        -- 業界
  founded_year INTEGER,                 -- 設立年
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 記事メタデータ（不変）
CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,                 -- 'PR_TIMES', 'LINKEDIN', etc
  url TEXT NOT NULL UNIQUE,            -- 記事の一意識別子
  first_scraped_at DATETIME NOT NULL,  -- 初回発見日時
  last_scraped_at DATETIME NOT NULL,   -- 最終確認日時
  scrape_count INTEGER DEFAULT 1,      -- スクレイプ回数
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 記事データ（履歴管理）
CREATE TABLE IF NOT EXISTS article_contents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT,                         -- 本文（将来拡張用）
  summary TEXT,                         -- 要約（将来拡張用）
  published_at DATETIME,                -- 記事の公開日時
  scraped_at DATETIME NOT NULL,        -- このデータの取得日時
  is_latest BOOLEAN DEFAULT TRUE,      -- 最新版フラグ
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (article_id) REFERENCES articles(id)
);

-- 記事-企業リレーション（多対多）
CREATE TABLE IF NOT EXISTS article_companies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id INTEGER NOT NULL,
  company_id INTEGER NOT NULL,
  confidence REAL DEFAULT 1.0,         -- 抽出信頼度 (0.0-1.0)
  extraction_method TEXT,               -- 'title', 'content', 'manual'
  position INTEGER,                     -- 記事内での出現位置
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(article_id, company_id),
  FOREIGN KEY (article_id) REFERENCES articles(id),
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- スクレイピング実行ログ
CREATE TABLE IF NOT EXISTS scraping_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  keyword TEXT,
  started_at DATETIME NOT NULL,
  completed_at DATETIME,
  article_count INTEGER DEFAULT 0,
  new_article_count INTEGER DEFAULT 0,
  updated_article_count INTEGER DEFAULT 0,
  status TEXT DEFAULT 'running',       -- 'running', 'completed', 'failed'
  error_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- スクレイピング実行と記事の関連
CREATE TABLE IF NOT EXISTS scraping_run_articles (
  scraping_run_id INTEGER NOT NULL,
  article_id INTEGER NOT NULL,
  is_new BOOLEAN DEFAULT TRUE,         -- 新規発見かどうか
  PRIMARY KEY (scraping_run_id, article_id),
  FOREIGN KEY (scraping_run_id) REFERENCES scraping_runs(id),
  FOREIGN KEY (article_id) REFERENCES articles(id)
);

-- ========================================
-- KuzuDB連携用リレーションテーブル
-- ========================================

-- 企業間の共起関係（同じ記事に出現）
CREATE TABLE IF NOT EXISTS company_co_occurrences (
  company1_id INTEGER NOT NULL,
  company2_id INTEGER NOT NULL,
  article_id INTEGER NOT NULL,
  strength REAL DEFAULT 1.0,           -- 関係の強さ
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (company1_id, company2_id, article_id),
  FOREIGN KEY (company1_id) REFERENCES companies(id),
  FOREIGN KEY (company2_id) REFERENCES companies(id),
  FOREIGN KEY (article_id) REFERENCES articles(id),
  CHECK (company1_id < company2_id)    -- 順序を保証して重複防止
);

-- 企業の時系列出現（グラフ分析用）
CREATE TABLE IF NOT EXISTS company_timeline (
  company_id INTEGER NOT NULL,
  date DATE NOT NULL,
  article_count INTEGER DEFAULT 0,
  total_confidence REAL DEFAULT 0.0,
  PRIMARY KEY (company_id, date),
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ========================================
-- インデックス
-- ========================================

-- 検索性能向上
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_scraped ON articles(last_scraped_at);
CREATE INDEX IF NOT EXISTS idx_article_contents_article ON article_contents(article_id);
CREATE INDEX IF NOT EXISTS idx_article_contents_latest ON article_contents(is_latest);
CREATE INDEX IF NOT EXISTS idx_article_companies_article ON article_companies(article_id);
CREATE INDEX IF NOT EXISTS idx_article_companies_company ON article_companies(company_id);
CREATE INDEX IF NOT EXISTS idx_companies_normalized ON companies(normalized_name);

-- KuzuDB連携用
CREATE INDEX IF NOT EXISTS idx_co_occurrence_company1 ON company_co_occurrences(company1_id);
CREATE INDEX IF NOT EXISTS idx_co_occurrence_company2 ON company_co_occurrences(company2_id);
CREATE INDEX IF NOT EXISTS idx_timeline_date ON company_timeline(date);

-- ========================================
-- トリガー
-- ========================================

-- article_contentsに新規追加時、既存のis_latestをfalseに
CREATE TRIGGER IF NOT EXISTS update_latest_content
BEFORE INSERT ON article_contents
BEGIN
  UPDATE article_contents 
  SET is_latest = FALSE 
  WHERE article_id = NEW.article_id AND is_latest = TRUE;
END;

-- companiesの更新日時自動更新
CREATE TRIGGER IF NOT EXISTS update_companies_timestamp
AFTER UPDATE ON companies
BEGIN
  UPDATE companies 
  SET updated_at = CURRENT_TIMESTAMP 
  WHERE id = NEW.id;
END;

-- ========================================
-- ビュー（よく使うクエリ）
-- ========================================

-- 最新の記事内容を含む記事一覧
CREATE VIEW IF NOT EXISTS v_latest_articles AS
SELECT 
  a.id,
  a.source,
  a.url,
  ac.title,
  ac.content,
  ac.published_at,
  a.first_scraped_at,
  a.last_scraped_at,
  a.scrape_count
FROM articles a
JOIN article_contents ac ON a.id = ac.article_id AND ac.is_latest = TRUE;

-- 企業別記事数ランキング
CREATE VIEW IF NOT EXISTS v_company_article_stats AS
SELECT 
  c.id,
  c.name,
  COUNT(DISTINCT ac.article_id) as article_count,
  AVG(ac.confidence) as avg_confidence,
  MAX(a.last_scraped_at) as last_mentioned
FROM companies c
JOIN article_companies ac ON c.id = ac.company_id
JOIN articles a ON ac.article_id = a.id
GROUP BY c.id, c.name
ORDER BY article_count DESC;