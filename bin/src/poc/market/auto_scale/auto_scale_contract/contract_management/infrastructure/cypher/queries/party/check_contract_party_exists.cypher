/*
 * Check if ContractParty Relationship Exists
 * 
 * Verifies whether a specific party is already associated with a contract
 * in a particular role. Used to prevent duplicate relationships.
 *
 * Parameters:
 * - $contract_id: ID of the contract
 * - $party_id: ID of the party
 * - $role: Role to check for ('buyer' or 'seller')
 *
 * Returns:
 * - The relationship if it exists
 * - Empty result if no relationship exists
 *
 * Example usage:
 * CALL {
 *   contract_id: 'CONTRACT001',
 *   party_id: 'PARTY001',
 *   role: 'buyer'
 * }
 */

MATCH (c:Contract)-[cp:ContractParty]->(p:Party)
WHERE c.id = $contract_id 
  AND p.id = $party_id 
  AND cp.role = $role
RETURN cp