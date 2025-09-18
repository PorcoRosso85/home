-- Purpose: Check if a contract-party relationship exists
-- Description: Verifies whether a specific relationship between a contract
--              and a party with a given role already exists
-- Parameters:
--   $contract_id: STRING - Unique contract identifier
--   $party_id: STRING - Unique party identifier
--   $role: STRING - Role in the contract ('buyer' or 'seller')
-- Returns:
--   cp: ContractParty relationship if exists, null otherwise

MATCH (c:Contract)-[cp:ContractParty]->(p:Party)
WHERE c.id = $contract_id AND p.id = $party_id AND cp.role = $role
RETURN cp