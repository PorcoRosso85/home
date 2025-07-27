-- Purpose: Create a relationship between a contract and a party
-- Description: Establishes a ContractParty relationship between an existing
--              contract and party with a specified role
-- Parameters:
--   $contract_id: STRING - Unique contract identifier
--   $party_id: STRING - Unique party identifier
--   $role: STRING - Role in the contract ('buyer' or 'seller')
--   $joined_at: STRING - ISO format timestamp when party joined the contract
-- Prerequisites:
--   - Both Contract and Party nodes must exist before creating the relationship

MATCH (c:Contract) WHERE c.id = $contract_id
MATCH (p:Party) WHERE p.id = $party_id
CREATE (c)-[cp:ContractParty {
    role: $role,
    joined_at: $joined_at
}]->(p)