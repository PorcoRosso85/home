-- ============================================
-- 最終系DDL v2 検証クエリ
-- 全7ユースケースの動作確認
-- ============================================

-- ============================================
-- UC1: 貢献度ランキング
-- 「結局、どのパートナーが一番『儲かる』顧客を連れてきてるんだ？」
-- ============================================
-- パートナーが紹介した顧客のLTV合計でランキング
MATCH (p:Entity {type: 'partner'})-[i:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
MATCH (c)-[:HAS_CONTRACT]->(s:Contract {type: 'subscription'})
RETURN 
  p.name AS パートナー名,
  COUNT(c) AS 顧客数,
  SUM(s.recurring_amount * s.duration) AS LTV合計
ORDER BY LTV合計 DESC;

-- ============================================
-- UC2: パートナーROIの可視化  
-- 「この報酬プラン、本当にウチは損してないか？払いすぎてないか？」
-- ============================================
-- 顧客価値から支払い額を差し引いて純利益を算出
MATCH (p:Entity {type: 'partner'})
MATCH (c:Entity {type: 'customer'})-[i:INTERACTION {type: 'introduced'}]<-(p)
MATCH (r:Reward {entity_id: p.id, status: 'paid'})
WITH p, SUM(c.ltv) AS 総顧客価値, SUM(r.amount) AS 総支払額
RETURN 
  p.name AS パートナー名,
  総顧客価値,
  総支払額,
  総顧客価値 - 総支払額 AS 純利益,
  CASE 
    WHEN 総支払額 > 0 THEN (総顧客価値 - 総支払額) / 総支払額 * 100
    ELSE 100
  END AS ROI_率
ORDER BY 純利益 DESC;

-- ============================================
-- UC3: 報酬プランの未来予測シミュレーション
-- 「A社に提案するプラン、XとY、どっちが最終的に儲かるんだ？」
-- ============================================
-- プランX: 20%固定
WITH 0.20 AS rate_x
MATCH (c:Entity {type: 'customer', source: 'referral'})
WITH '20%固定' AS プラン名, SUM(c.ltv * rate_x) AS 予測支払額, SUM(c.ltv) AS 総顧客価値
RETURN プラン名, 予測支払額, 総顧客価値 - 予測支払額 AS 予測利益

UNION ALL

-- プランY: 階層型15-35%
WITH 0.15 AS rate_low, 0.25 AS rate_mid, 0.35 AS rate_high
MATCH (c:Entity {type: 'customer', source: 'referral'})
WITH '階層型15-35%' AS プラン名,
  SUM(CASE 
    WHEN c.ltv < 100000 THEN c.ltv * rate_low
    WHEN c.ltv < 500000 THEN c.ltv * rate_mid  
    ELSE c.ltv * rate_high
  END) AS 予測支払額,
  SUM(c.ltv) AS 総顧客価値
RETURN プラン名, 予測支払額, 総顧客価値 - 予測支払額 AS 予測利益;

-- ============================================
-- UC4: 優良顧客プロファイルの抽出
-- 「ウチの『神』パートナーAさんが連れてくる客、なんか他と違う気がする…」
-- ============================================
-- 特定パートナーが紹介した顧客の共通特性を分析
MATCH (p:Entity {type: 'partner', name: '優良パートナーA'})-[:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
RETURN 
  c.industry AS 業種,
  COUNT(c) AS 顧客数,
  AVG(c.ltv) AS 平均LTV,
  AVG(c.retention_rate) AS 平均継続率,
  MIN(c.ltv) AS 最小LTV,
  MAX(c.ltv) AS 最大LTV
GROUP BY c.industry
ORDER BY 平均LTV DESC;

-- ============================================
-- UC5: 顧客定着率の比較分析
-- 「パートナー経由の客って、本当に長く使ってくれるのか？」
-- ============================================
-- 獲得元別の顧客品質比較
MATCH (c:Entity {type: 'customer'})
RETURN 
  c.source AS 獲得元,
  COUNT(c) AS 顧客数,
  AVG(c.retention_rate) AS 平均継続率,
  AVG(c.ltv) AS 平均LTV,
  CASE 
    WHEN c.source = 'referral' THEN 'パートナー経由'
    WHEN c.source = 'direct' THEN '直接獲得'
    WHEN c.source = 'ad' THEN '広告経由'
    ELSE 'その他'
  END AS 獲得チャネル
GROUP BY c.source
ORDER BY 平均継続率 DESC;

-- ============================================
-- UC6: パートナー間の隠れた関係性の発見
-- 「最近活躍のBさん、実は神パートナーAさんと繋がりがあったりして？」
-- ============================================
-- パートナー間の様々な関係性パスを探索
MATCH path = shortestPath(
  (a:Entity {type: 'partner', name: 'パートナーA'})-[:INTERACTION*..3]-(b:Entity {type: 'partner', name: 'パートナーB'})
)
WHERE ALL(r IN relationships(path) WHERE r.type IN ['connected', 'worked_with', 'introduced'])
RETURN 
  [n IN nodes(path) | n.name] AS 関係パス,
  [r IN relationships(path) | r.type] AS 関係タイプ,
  length(path) AS 関係の深さ,
  [r IN relationships(path) | r.metadata] AS 詳細情報;

-- ============================================
-- UC7: 貢献パス（アトリビューション）の可視化
-- 「この顧客、パートナーA経由だけど、Web広告も踏んでる。どっちの貢献？」
-- ============================================
-- 顧客獲得に至る全タッチポイントを時系列で可視化
MATCH (c:Entity {type: 'customer', name: '特定顧客'})
OPTIONAL MATCH (ad:Entity {type: 'campaign'})-[click:INTERACTION {type: 'clicked'}]->(c)
OPTIONAL MATCH (p:Entity {type: 'partner'})-[intro:INTERACTION {type: 'introduced'}]->(c)
RETURN 
  c.name AS 顧客名,
  ad.name AS 広告キャンペーン,
  click.interaction_date AS 広告クリック日時,
  p.name AS 紹介パートナー,
  intro.interaction_date AS 紹介日時,
  CASE 
    WHEN click.interaction_date < intro.interaction_date THEN '広告→パートナー'
    WHEN intro.interaction_date < click.interaction_date THEN 'パートナー→広告'
    WHEN click.interaction_date IS NULL THEN 'パートナーのみ'
    WHEN intro.interaction_date IS NULL THEN '広告のみ'
    ELSE '同時'
  END AS 貢献順序
ORDER BY c.name;