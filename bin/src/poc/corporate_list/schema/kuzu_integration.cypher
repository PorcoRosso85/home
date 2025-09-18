-- ========================================
-- KuzuDB連携用Cypherクエリ
-- SQLiteデータをグラフとして分析
-- ========================================

-- 前提: SQLiteデータベースをKuzuDBにアタッチ
-- ATTACH DATABASE './corporate_leads.db' AS sqlite_db (DBTYPE SQLITE);

-- ========================================
-- 1. 企業ネットワーク分析
-- ========================================

-- 同じ記事に出現する企業の関係性
MATCH (c1:companies)-[:MENTIONED_IN]->(a:articles)<-[:MENTIONED_IN]-(c2:companies)
WHERE c1.id < c2.id
RETURN c1.name, c2.name, COUNT(DISTINCT a.id) as co_occurrences
ORDER BY co_occurrences DESC
LIMIT 20;

-- 特定企業の関連企業ネットワーク（1ホップ）
MATCH (target:companies {name: '株式会社サンプル'})-[:MENTIONED_IN]->(a:articles)<-[:MENTIONED_IN]-(related:companies)
WHERE target.id != related.id
RETURN related.name, COUNT(DISTINCT a.id) as connection_strength
ORDER BY connection_strength DESC;

-- ========================================
-- 2. 時系列パターン分析
-- ========================================

-- 企業の出現頻度の時系列変化
MATCH (c:companies)-[:MENTIONED_IN]->(a:articles)
WHERE c.name = '株式会社サンプル'
RETURN DATE(a.last_scraped_at) as date, COUNT(*) as mentions
ORDER BY date;

-- 急成長企業の検出（過去7日 vs その前7日）
MATCH (c:companies)-[:MENTIONED_IN]->(a_recent:articles)
WHERE a_recent.last_scraped_at > datetime('now', '-7 days')
WITH c, COUNT(DISTINCT a_recent.id) as recent_count
MATCH (c)-[:MENTIONED_IN]->(a_prev:articles)
WHERE a_prev.last_scraped_at <= datetime('now', '-7 days') 
  AND a_prev.last_scraped_at > datetime('now', '-14 days')
WITH c.name as company, recent_count, COUNT(DISTINCT a_prev.id) as prev_count
WHERE recent_count > prev_count * 1.5
RETURN company, recent_count, prev_count, 
       ROUND((recent_count - prev_count) * 100.0 / prev_count, 2) as growth_rate
ORDER BY growth_rate DESC;

-- ========================================
-- 3. グラフ探索クエリ
-- ========================================

-- 2つの企業間の最短パス（共通記事経由）
MATCH path = shortestPath(
  (c1:companies {name: '企業A'})-[:MENTIONED_IN*..4]-(c2:companies {name: '企業B'})
)
RETURN path;

-- 企業のインフルエンス度（多くの企業と共起）
MATCH (c:companies)-[:MENTIONED_IN]->(a:articles)<-[:MENTIONED_IN]-(other:companies)
WHERE c.id != other.id
WITH c, COUNT(DISTINCT other.id) as connected_companies, COUNT(DISTINCT a.id) as shared_articles
RETURN c.name, connected_companies, shared_articles, 
       ROUND(shared_articles * 1.0 / connected_companies, 2) as avg_connections
ORDER BY connected_companies DESC
LIMIT 20;

-- ========================================
-- 4. コミュニティ検出
-- ========================================

-- 密接に関連する企業グループ（3社以上が相互に言及）
MATCH (c1:companies)-[:MENTIONED_IN]->(a1:articles)<-[:MENTIONED_IN]-(c2:companies),
      (c2)-[:MENTIONED_IN]->(a2:articles)<-[:MENTIONED_IN]-(c3:companies),
      (c3)-[:MENTIONED_IN]->(a3:articles)<-[:MENTIONED_IN]-(c1)
WHERE c1.id < c2.id AND c2.id < c3.id
RETURN c1.name, c2.name, c3.name, 
       COUNT(DISTINCT a1.id) + COUNT(DISTINCT a2.id) + COUNT(DISTINCT a3.id) as total_mentions
ORDER BY total_mentions DESC;

-- ========================================
-- 5. 異常検知
-- ========================================

-- 突発的に言及が増えた企業
MATCH (c:companies)-[:MENTIONED_IN]->(a:articles)
WHERE DATE(a.last_scraped_at) = DATE('now')
WITH c, COUNT(*) as today_count
MATCH (c)-[:MENTIONED_IN]->(a_past:articles)
WHERE a_past.last_scraped_at < datetime('now', '-1 day')
  AND a_past.last_scraped_at > datetime('now', '-8 days')
WITH c.name as company, today_count, AVG(COUNT(a_past.id)) as avg_past_week
WHERE today_count > avg_past_week * 3
RETURN company, today_count, ROUND(avg_past_week, 2) as avg_past_week,
       ROUND(today_count / avg_past_week, 2) as spike_ratio
ORDER BY spike_ratio DESC;

-- ========================================
-- 6. データ品質分析
-- ========================================

-- 企業名抽出の精度分析
MATCH (a:articles)
OPTIONAL MATCH (a)<-[r:MENTIONED_IN]-(c:companies)
WITH a, COUNT(c) as company_count, AVG(r.confidence) as avg_confidence
RETURN 
  CASE 
    WHEN company_count = 0 THEN '企業なし'
    WHEN company_count = 1 THEN '1社'
    WHEN company_count = 2 THEN '2社'
    ELSE '3社以上'
  END as category,
  COUNT(*) as article_count,
  ROUND(AVG(avg_confidence), 3) as avg_extraction_confidence
ORDER BY category;