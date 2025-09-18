-- Purpose: Find a contract by its unique identifier
-- Description: Retrieves a contract node along with all related parties
--              through ContractParty relationships
-- Parameters:
--   $id: STRING - Unique contract identifier (UUID as string)
-- Returns:
--   c: Contract node with all properties
--   parties: Collection of party nodes with their relationships
--            Each party object contains {party: Party node, relationship: ContractParty edge}

MATCH (c:Contract) 
WHERE c.id = $id
OPTIONAL MATCH (c)-[cp:ContractParty]->(p:Party)
RETURN c, collect({party: p, relationship: cp}) as parties