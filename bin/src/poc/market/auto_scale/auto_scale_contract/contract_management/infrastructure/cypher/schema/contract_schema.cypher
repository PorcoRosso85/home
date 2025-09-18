-- ============================================================================
-- Contract Management System - Kuzu GraphDB Schema
-- ============================================================================
-- Purpose: Define the graph database schema for multi-level contract management
-- Database: Kuzu
-- Created: 2025-01-27
-- ============================================================================

-- ============================================================================
-- NODE TABLES
-- ============================================================================

-- Contract Node: Represents a contract in the multi-level contract system
CREATE NODE TABLE Contract(
    id STRING PRIMARY KEY,
    title STRING,                -- Contract title
    description STRING,          -- Contract description
    type STRING,                 -- 'reseller', 'referral', 'community', 'value_chain'
    status STRING,               -- 'draft', 'active', 'expired', 'terminated'
    value_amount STRING,         -- Contract value amount (stored as string for Decimal)
    value_currency STRING,       -- Currency code
    payment_terms STRING,        -- Payment terms
    terms STRING,                -- Contract terms as JSON string
    created_at STRING,           -- ISO format timestamp
    expires_at STRING,           -- ISO format timestamp
    updated_at STRING            -- ISO format timestamp
);

-- Party Node: Represents contract parties (companies or individuals)
CREATE NODE TABLE Party(
    id STRING PRIMARY KEY,
    name STRING,                 -- Party name
    type STRING,                 -- 'company', 'individual'
    tax_id STRING,               -- Tax identification number
    created_at STRING            -- ISO format timestamp
);

-- ============================================================================
-- RELATIONSHIP TABLES
-- ============================================================================

-- ParentContract: Defines parent-child relationships between contracts
CREATE REL TABLE ParentContract(
    FROM Contract TO Contract,
    inheritance_type STRING,     -- 'full', 'partial', 'none'
    inherited_terms STRING,      -- Terms inherited from parent contract (JSON string)
    created_at STRING            -- ISO format timestamp
);

-- ContractParty: Links contracts to their parties with specific roles
CREATE REL TABLE ContractParty(
    FROM Contract TO Party,
    role STRING,                 -- 'buyer', 'seller', 'referrer', 'guarantor'
    commission_rate DOUBLE,      -- Commission rate for this party in this contract
    special_terms STRING,        -- Party-specific special terms (JSON string)
    joined_at STRING             -- ISO format timestamp
);

-- ReferralChain: Tracks referral relationships between parties
CREATE REL TABLE ReferralChain(
    FROM Party TO Party,
    contract_id STRING,          -- ID of the contract governing this referral
    referral_date STRING,        -- ISO format timestamp
    commission_rate DOUBLE       -- Commission rate for this referral
);

-- ============================================================================
-- INDEXES (Optional - add based on query patterns)
-- ============================================================================

-- CREATE INDEX idx_contract_type ON Contract(type);
-- CREATE INDEX idx_contract_status ON Contract(status);
-- CREATE INDEX idx_party_type ON Party(type);
-- CREATE INDEX idx_contractparty_role ON ContractParty(role);