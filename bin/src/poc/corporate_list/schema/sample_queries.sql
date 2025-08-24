-- ========================================
-- サンプルクエリ集
-- ========================================

-- 1. 新規記事の挿入（UPSERT）
-- まず記事の存在確認、なければ挿入
INSERT INTO articles (source, url, first_scraped_at, last_scraped_at)
VALUES ('PR_TIMES', 'https://example.com/article1', datetime('now'), datetime('now'))
ON CONFLICT(url) DO UPDATE SET
  last_scraped_at = datetime('now'),
  scrape_count = scrape_count + 1;

-- 記事内容の追加（履歴として保存）
INSERT INTO article_contents (article_id, title, scraped_at)
VALUES (
  (SELECT id FROM articles WHERE url = 'https://example.com/article1'),
  '新製品発表のお知らせ',
  datetime('now')
);

-- 2. 企業の正規化と登録
-- 企業名の正規化（カタカナ変換、株式会社除去等はアプリ側で）
INSERT OR IGNORE INTO companies (name, normalized_name)
VALUES ('株式会社サンプル', 'サンプル');

-- 3. 記事と企業の関連付け
INSERT INTO article_companies (article_id, company_id, confidence, extraction_method)
VALUES (
  (SELECT id FROM articles WHERE url = 'https://example.com/article1'),
  (SELECT id FROM companies WHERE name = '株式会社サンプル'),
  0.95,
  'title'
);

-- 4. 企業の共起関係を記録（KuzuDB連携用）
INSERT INTO company_co_occurrences (company1_id, company2_id, article_id)
SELECT 
  CASE WHEN c1.id < c2.id THEN c1.id ELSE c2.id END,
  CASE WHEN c1.id < c2.id THEN c2.id ELSE c1.id END,
  ac1.article_id
FROM article_companies ac1
JOIN article_companies ac2 ON ac1.article_id = ac2.article_id
JOIN companies c1 ON ac1.company_id = c1.id
JOIN companies c2 ON ac2.company_id = c2.id
WHERE c1.id != c2.id;

-- ========================================
-- 分析クエリ
-- ========================================

-- 5. 過去7日間のトレンド企業
SELECT 
  c.name,
  COUNT(DISTINCT a.id) as recent_articles,
  GROUP_CONCAT(DISTINCT DATE(a.last_scraped_at)) as active_days
FROM companies c
JOIN article_companies ac ON c.id = ac.company_id
JOIN articles a ON ac.article_id = a.id
WHERE a.last_scraped_at > datetime('now', '-7 days')
GROUP BY c.id
ORDER BY recent_articles DESC
LIMIT 10;

-- 6. 企業の時系列出現パターン
SELECT 
  c.name,
  DATE(a.last_scraped_at) as date,
  COUNT(*) as article_count
FROM companies c
JOIN article_companies ac ON c.id = ac.company_id
JOIN articles a ON ac.article_id = a.id
WHERE c.name = '株式会社サンプル'
GROUP BY c.id, DATE(a.last_scraped_at)
ORDER BY date;

-- 7. 記事内容の変更履歴
SELECT 
  ac.id,
  ac.title,
  ac.scraped_at,
  ac.is_latest,
  CASE 
    WHEN LAG(ac.title) OVER (ORDER BY ac.scraped_at) != ac.title 
    THEN 'タイトル変更'
    ELSE '変更なし'
  END as change_type
FROM article_contents ac
WHERE ac.article_id = 1
ORDER BY ac.scraped_at DESC;

-- 8. 企業の共起ネットワーク（よく一緒に言及される企業）
SELECT 
  c1.name as company1,
  c2.name as company2,
  COUNT(*) as co_occurrence_count,
  GROUP_CONCAT(a.url) as article_urls
FROM company_co_occurrences co
JOIN companies c1 ON co.company1_id = c1.id
JOIN companies c2 ON co.company2_id = c2.id
JOIN articles a ON co.article_id = a.id
GROUP BY co.company1_id, co.company2_id
ORDER BY co_occurrence_count DESC
LIMIT 20;

-- 9. スクレイピング実行統計
SELECT 
  sr.id,
  sr.source,
  sr.keyword,
  sr.started_at,
  sr.completed_at,
  sr.article_count,
  sr.new_article_count,
  ROUND((sr.new_article_count * 100.0 / sr.article_count), 2) as new_rate_percent,
  sr.status
FROM scraping_runs sr
ORDER BY sr.started_at DESC
LIMIT 10;

-- 10. データ品質チェック
-- 企業名が抽出できていない記事
SELECT 
  a.url,
  ac.title,
  a.source,
  a.last_scraped_at
FROM articles a
JOIN article_contents ac ON a.id = ac.article_id AND ac.is_latest = TRUE
LEFT JOIN article_companies aco ON a.id = aco.article_id
WHERE aco.id IS NULL
ORDER BY a.last_scraped_at DESC;