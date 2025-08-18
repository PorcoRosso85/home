-- ============================================
-- KuzuDB DDL for SaaS Partner Calculator
-- Browser WASM Optimized Version with DB-side Calculations
-- ============================================

-- Core Node Tables
-- ============================================

-- Partner: Unified entity (customers can become partners)
CREATE NODE TABLE Partner(
  id SERIAL PRIMARY KEY,
  code STRING NOT NULL,           -- Unique partner identifier
  name STRING,                    -- Partner display name
  tier STRING,                    -- Current tier level
  value DECIMAL(15,2),           -- Associated value (revenue, volume, etc.)
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP),
  updated_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- RewardRule: Defines various reward calculation methods
CREATE NODE TABLE RewardRule(
  id SERIAL PRIMARY KEY,
  name STRING NOT NULL,           -- Rule identifier
  type STRING NOT NULL,           -- 'fixed', 'percentage', 'tiered', 'network'
  base_amount DECIMAL(15,2),     -- Base reward amount (for fixed type)
  base_rate DECIMAL(5,4),        -- Base percentage rate (for percentage type)
  parameters STRING,              -- JSON format for complex rules
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- Threshold: Defines tier boundaries for tiered calculations
CREATE NODE TABLE Threshold(
  id SERIAL PRIMARY KEY,
  rule_id INT64,                  -- Associated reward rule
  metric STRING NOT NULL,         -- What metric this threshold applies to
  min_value DECIMAL(15,2),       -- Minimum value for this tier
  max_value DECIMAL(15,2),       -- Maximum value for this tier (NULL for open-ended)
  rate DECIMAL(5,4),             -- Rate applied in this tier
  bonus DECIMAL(15,2),           -- Additional bonus for this tier
  sequence INT32                  -- Order of threshold application
);

-- Transaction: Records of transactions that trigger rewards
CREATE NODE TABLE Transaction(
  id SERIAL PRIMARY KEY,
  partner_id INT64 NOT NULL,      -- Partner who made the transaction
  amount DECIMAL(15,2) NOT NULL,  -- Transaction amount
  type STRING,                    -- Transaction type
  status STRING DEFAULT 'pending', -- 'pending', 'confirmed', 'cancelled'
  transaction_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- Reward: Calculated rewards (results of DB-side calculations)
CREATE NODE TABLE Reward(
  id SERIAL PRIMARY KEY,
  partner_id INT64 NOT NULL,      -- Partner receiving the reward
  rule_id INT64 NOT NULL,         -- Rule used for calculation
  transaction_id INT64,           -- Associated transaction (if applicable)
  amount DECIMAL(15,2) NOT NULL,  -- Calculated reward amount
  calculation_params STRING,      -- JSON format of parameters used
  period_start DATE,              -- Reward period start
  period_end DATE,                -- Reward period end
  status STRING DEFAULT 'pending', -- 'pending', 'approved', 'paid'
  created_at TIMESTAMP DEFAULT CAST(CURRENT_TIMESTAMP AS TIMESTAMP)
);

-- Relationship Tables
-- ============================================

-- REFERS: Partner network relationships (who referred whom)
CREATE REL TABLE REFERS(
  FROM Partner TO Partner,
  referred_date DATE NOT NULL,
  depth INT32 DEFAULT 1,          -- Network depth from referrer
  status STRING DEFAULT 'active'   -- 'active', 'inactive'
);

-- APPLIES_RULE: Links partners to their applicable reward rules
CREATE REL TABLE APPLIES_RULE(
  FROM Partner TO RewardRule,
  start_date DATE NOT NULL,
  end_date DATE,                  -- NULL for currently active rules
  priority INT32 DEFAULT 0        -- Rule application priority
);

-- HAS_THRESHOLD: Links reward rules to their thresholds
CREATE REL TABLE HAS_THRESHOLD(
  FROM RewardRule TO Threshold
);

-- TRIGGERED_BY: Links rewards to their triggering transactions
CREATE REL TABLE TRIGGERED_BY(
  FROM Reward TO Transaction
);