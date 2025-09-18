-- Purpose: Find all contracts for a specific client
-- Description: Retrieves contracts where the specified party is the buyer (client)
--              Returns each contract with all associated parties
-- Parameters:
--   $client_id: STRING - Unique identifier of the client party
-- Returns:
--   c: Contract node with all properties
--   parties: Collection of all party nodes related to each contract
--            Each party object contains {party: Party node, relationship: ContractParty edge}

MATCH (c:Contract)-[cp1:ContractParty]->(client:Party) 
WHERE cp1.role = 'buyer' AND client.id = $client_id
OPTIONAL MATCH (c)-[cp2:ContractParty]->(p:Party)
RETURN c, collect({party: p, relationship: cp2}) as parties