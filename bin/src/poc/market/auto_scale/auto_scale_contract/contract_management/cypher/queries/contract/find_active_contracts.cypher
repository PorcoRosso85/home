-- Purpose: Find all contracts with active status
-- Description: Retrieves all contract nodes that have status 'ACTIVE'
--              along with their associated parties
-- Parameters:
--   $status: STRING - Contract status to filter by (should be 'ACTIVE')
-- Returns:
--   c: Contract node with all properties
--   parties: Collection of party nodes with their relationships
--            Each party object contains {party: Party node, relationship: ContractParty edge}

MATCH (c:Contract) 
WHERE c.status = $status
OPTIONAL MATCH (c)-[cp:ContractParty]->(p:Party)
RETURN c, collect({party: p, relationship: cp}) as parties