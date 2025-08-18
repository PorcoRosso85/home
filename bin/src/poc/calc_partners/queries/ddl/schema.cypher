-- ============================================
-- KuzuDB DDL for SaaS Partner Calculator
-- Browser WASM Optimized Version
-- ============================================

-- Core Entities
-- ============================================

-- Unified Entity (Partner/Customer)
CREATE NODE TABLE Entity(
  id SERIAL PRIMARY KEY,
  name STRING NOT NULL,
  type STRING,  -- 'partner' | 'customer' | 'both'
  status STRING DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction Records
CREATE NODE TABLE Transaction(
  id SERIAL PRIMARY KEY,
  amount DECIMAL(15,2) NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  type STRING DEFAULT 'revenue'
);

-- Reward Structure Definition
CREATE NODE TABLE RewardStructure(
  id SERIAL PRIMARY KEY,
  name STRING NOT NULL,
  type STRING NOT NULL,  -- 'percentage' | 'fixed' | 'tiered'
  rate DECIMAL(5,4),
  fixed_amount DECIMAL(10,2),
  tiers STRING  -- JSON format for tier information
);

-- Cost Tracking
CREATE NODE TABLE Cost(
  id SERIAL PRIMARY KEY,
  amount DECIMAL(15,2) NOT NULL,
  type STRING NOT NULL,  -- 'marketing' | 'operational' | 'acquisition'
  timestamp TIMESTAMP NOT NULL
);

-- Simulation Results Storage
CREATE NODE TABLE SimulationResult(
  id SERIAL PRIMARY KEY,
  scenario_name STRING NOT NULL,
  query_type STRING NOT NULL,  -- 'roi' | 'ltv' | 'cpa' | 'tiered_rate' etc
  input_params STRING NOT NULL,  -- JSON
  output_data STRING NOT NULL,   -- JSON
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationships
-- ============================================

-- Partner contribution to transactions
CREATE REL TABLE CONTRIBUTED_TO(
  FROM Entity TO Transaction,
  contribution_score DECIMAL(3,2) DEFAULT 1.0
);

-- Customer acquisition by partners
CREATE REL TABLE ACQUIRED(
  FROM Entity TO Entity,
  acquisition_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  channel STRING
);

-- Customer purchase transactions
CREATE REL TABLE PURCHASED(
  FROM Entity TO Transaction,
  purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reward structure assignment
CREATE REL TABLE HAS_REWARD_STRUCTURE(
  FROM Entity TO RewardStructure,
  effective_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  effective_to TIMESTAMP
);

-- Cost allocation to entities
CREATE REL TABLE INCURRED_COST(
  FROM Entity TO Cost,
  allocation_ratio DECIMAL(3,2) DEFAULT 1.0
);