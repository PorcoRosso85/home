-- Test Schema for KuzuGraphRepository
-- This schema is used specifically for testing purposes

-- Create Contract node table
CREATE NODE TABLE IF NOT EXISTS Contract (
    contract_id STRING PRIMARY KEY,
    title STRING,
    description STRING,
    client_id STRING,
    client_name STRING,
    client_email STRING,
    vendor_id STRING,
    vendor_name STRING,
    vendor_email STRING,
    value_amount STRING,
    value_currency STRING,
    start_date STRING,
    end_date STRING,
    payment_terms STRING,
    status STRING,
    created_at STRING,
    updated_at STRING
);

-- Create ContractTerm node table
CREATE NODE TABLE IF NOT EXISTS ContractTerm (
    term_id STRING PRIMARY KEY,
    title STRING,
    description STRING,
    is_mandatory BOOLEAN
);

-- Create relationship table for contract terms
CREATE REL TABLE IF NOT EXISTS HAS_TERM (
    FROM Contract TO ContractTerm
);

-- Create parent-child relationship table for contracts
CREATE REL TABLE IF NOT EXISTS PARENT_OF (
    FROM Contract TO Contract,
    relationship_type STRING
);