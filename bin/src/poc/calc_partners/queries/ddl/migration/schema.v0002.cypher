-- ============================================
-- KuzuDB DDL for SaaS Partner Calculator
-- 中程度抽象化版 v2 - 全7ユースケース完全対応
-- ============================================

-- ============================================
-- Node Tables
-- ============================================

-- 汎用エンティティ（Partner/Customer/AdCampaign全て）
CREATE NODE TABLE Entity(
  id SERIAL PRIMARY KEY,
  code STRING NOT NULL,
  name STRING,
  type STRING NOT NULL,        -- 'partner', 'customer', 'campaign'
  -- Partner/Customer属性
  industry STRING,
  ltv DECIMAL(15,2),
  retention_rate DECIMAL(5,4),
  source STRING,               -- 'referral', 'direct', 'ad'
  -- Campaign属性  
  budget DECIMAL(15,2),
  campaign_type STRING,        -- 'web', 'social', 'email'
  -- 共通属性
  tier STRING,
  value DECIMAL(15,2),
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP),
  updated_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- 契約全般（Subscription/Transaction/広告支出）
CREATE NODE TABLE Contract(
  id SERIAL PRIMARY KEY,
  entity_id INT64 NOT NULL,
  type STRING NOT NULL,        -- 'subscription', 'transaction', 'ad_spend'
  amount DECIMAL(15,2),
  recurring_amount DECIMAL(15,2),  -- 月額（サブスク用）
  duration INT32,              -- 期間（月）
  status STRING DEFAULT 'active',
  start_date DATE,
  end_date DATE,
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- 報酬ルール
CREATE NODE TABLE RewardRule(
  id SERIAL PRIMARY KEY,
  name STRING NOT NULL,
  type STRING NOT NULL,        -- 'fixed', 'percentage', 'tiered', 'network'
  base_amount DECIMAL(15,2),
  base_rate DECIMAL(5,4),
  parameters STRING,           -- JSON形式の詳細パラメータ
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- 閾値（階層型報酬用）
CREATE NODE TABLE Threshold(
  id SERIAL PRIMARY KEY,
  rule_id INT64,
  metric STRING NOT NULL,
  min_value DECIMAL(15,2),
  max_value DECIMAL(15,2),
  rate DECIMAL(5,4),
  bonus DECIMAL(15,2),
  sequence INT32
);

-- 報酬記録（UC2対応: パートナーへの支払い記録）
CREATE NODE TABLE Reward(
  id SERIAL PRIMARY KEY,
  entity_id INT64 NOT NULL,    -- 報酬を受けるエンティティ
  rule_id INT64 NOT NULL,
  contract_id INT64,           -- 関連する契約
  amount DECIMAL(15,2) NOT NULL,
  calculation_params STRING,    -- JSON形式の計算パラメータ
  period_start DATE,
  period_end DATE,
  status STRING DEFAULT 'pending',  -- 'pending', 'approved', 'paid'
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- ============================================
-- Relationship Tables
-- ============================================

-- 汎用インタラクション（UC6対応: パートナー間関係も表現）
CREATE REL TABLE INTERACTION(
  FROM Entity TO Entity,
  type STRING NOT NULL,        -- 'introduced', 'referred', 'clicked', 'converted', 'connected', 'worked_with'
  interaction_date TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP),
  depth INT32 DEFAULT 1,       -- ネットワーク深度
  status STRING DEFAULT 'active',
  metadata STRING              -- JSON（詳細情報: 共通顧客、過去所属等）
);

-- エンティティと契約の関係
CREATE REL TABLE HAS_CONTRACT(
  FROM Entity TO Contract,
  role STRING                  -- 'owner', 'beneficiary', 'payer'
);

-- エンティティと報酬ルールの関係
CREATE REL TABLE APPLIES_RULE(
  FROM Entity TO RewardRule,
  start_date DATE NOT NULL,
  end_date DATE,
  priority INT32 DEFAULT 0
);

-- 報酬ルールと閾値の関係
CREATE REL TABLE HAS_THRESHOLD(
  FROM RewardRule TO Threshold
);

-- 報酬と契約の関係
CREATE REL TABLE TRIGGERED_BY(
  FROM Reward TO Contract
);

-- ============================================
-- 使用例とユースケース対応
-- ============================================

-- UC1: 貢献度ランキング
-- MATCH (p:Entity {type: 'partner'})-[i:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
-- MATCH (c)-[:HAS_CONTRACT]->(s:Contract {type: 'subscription'})
-- RETURN p.name, SUM(s.recurring_amount * s.duration) AS LTV合計

-- UC2: パートナーROI（Rewardテーブルで支払い記録完全対応）
-- MATCH (p:Entity {type: 'partner'})
-- MATCH (c:Entity {type: 'customer'})-[i:INTERACTION {type: 'introduced'}]<-(p)
-- MATCH (r:Reward {entity_id: p.id, status: 'paid'})
-- WITH p, SUM(c.ltv) AS 総顧客価値, SUM(r.amount) AS 総支払額
-- RETURN p.name, 総顧客価値 - 総支払額 AS 純利益

-- UC3: 報酬プランシミュレーション
-- WITH 0.3 AS virtual_rate
-- MATCH (c:Entity {type: 'customer', source: 'referral'})
-- RETURN SUM(c.ltv * virtual_rate) AS 予測支払額

-- UC4: 優良顧客プロファイルの抽出
-- MATCH (p:Entity {type: 'partner', name: 'Aさん'})-[:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
-- RETURN c.industry, AVG(c.ltv), AVG(c.retention_rate)

-- UC5: 顧客定着率の比較分析
-- MATCH (c:Entity {type: 'customer'})
-- RETURN c.source, AVG(c.retention_rate)
-- GROUP BY c.source

-- UC6: パートナー間の隠れた関係性（INTERACTION.metadataで詳細情報保持）
-- MATCH path = shortestPath(
--   (a:Entity {type: 'partner', name: 'A'})-[:INTERACTION*..3]-(b:Entity {type: 'partner', name: 'B'})
-- )
-- WHERE ALL(r IN relationships(path) WHERE r.type IN ['connected', 'worked_with', 'introduced'])
-- RETURN path

-- UC7: アトリビューション分析
-- MATCH (ad:Entity {type: 'campaign'})-[click:INTERACTION {type: 'clicked'}]->(c:Entity {type: 'customer'})
-- MATCH (p:Entity {type: 'partner'})-[intro:INTERACTION {type: 'introduced'}]->(c)
-- RETURN ad.name, p.name, c.name, click.interaction_date, intro.interaction_date