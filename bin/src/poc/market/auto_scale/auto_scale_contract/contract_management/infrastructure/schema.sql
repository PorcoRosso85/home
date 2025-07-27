-- Kuzu GraphDB Schema for Auto-Scale Contract Management System
-- Based on spec.md schema definition

-- ============================================================================
-- NODE TABLES
-- ============================================================================

-- Contract Node: Represents a contract in the multi-level contract system
CREATE NODE TABLE Contract(
    id STRING PRIMARY KEY,
    type STRING NOT NULL,        -- 'reseller', 'referral', 'community', 'value_chain'
    status STRING NOT NULL,      -- 'draft', 'active', 'expired', 'terminated'
    terms JSON,                  -- Contract terms as JSON
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Party Node: Represents contract parties (companies or individuals)
CREATE NODE TABLE Party(
    id STRING PRIMARY KEY,
    name STRING NOT NULL,
    type STRING NOT NULL,        -- 'company', 'individual'
    tax_id STRING,
    created_at TIMESTAMP NOT NULL
);

-- ============================================================================
-- RELATIONSHIP TABLES
-- ============================================================================

-- ParentContract: Defines parent-child relationships between contracts
CREATE REL TABLE ParentContract(
    FROM Contract TO Contract,
    inheritance_type STRING,     -- 'full', 'partial', 'none'
    inherited_terms JSON,        -- Terms inherited from parent contract
    created_at TIMESTAMP
);

-- ContractParty: Links contracts to their parties with specific roles
CREATE REL TABLE ContractParty(
    FROM Contract TO Party,
    role STRING NOT NULL,        -- 'buyer', 'seller', 'referrer', 'guarantor'
    commission_rate DOUBLE,      -- Commission rate for this party in this contract
    special_terms JSON,          -- Party-specific special terms
    joined_at TIMESTAMP NOT NULL
);

-- ReferralChain: Tracks referral relationships between parties
CREATE REL TABLE ReferralChain(
    FROM Party TO Party,
    contract_id STRING NOT NULL, -- ID of the contract governing this referral
    referral_date TIMESTAMP NOT NULL,
    commission_rate DOUBLE       -- Commission rate for this referral
);

-- ============================================================================
-- INDEXES (Optional - add based on query patterns)
-- ============================================================================

-- CREATE INDEX idx_contract_type ON Contract(type);
-- CREATE INDEX idx_contract_status ON Contract(status);
-- CREATE INDEX idx_party_type ON Party(type);
-- CREATE INDEX idx_contractparty_role ON ContractParty(role);

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Get all contracts for a specific party:
-- MATCH (p:Party {id: $party_id})-[:ContractParty]-(c:Contract)
-- RETURN c;

-- Get contract hierarchy starting from root:
-- MATCH path = (c:Contract)-[:ParentContract*0..]->(root:Contract)
-- WHERE NOT EXISTS { (root)-[:ParentContract]->(:Contract) }
-- RETURN path;

-- Get active referral chains:
-- MATCH chain = (referrer:Party)-[:ReferralChain*]->(referred:Party)
-- WHERE ALL(r IN relationships(chain) WHERE 
--     EXISTS { 
--         MATCH (c:Contract {id: r.contract_id})
--         WHERE c.status = 'active'
--     }
-- )
-- RETURN chain;