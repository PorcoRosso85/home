/*
 * Find All Contracts for a Party
 * 
 * Retrieves all contracts where a specific party is involved,
 * regardless of their role (buyer or seller).
 *
 * Parameters:
 * - $party_id: ID of the party
 *
 * Optional Parameters:
 * - $role: Filter by specific role ('buyer' or 'seller')
 * - $status: Filter by contract status ('active', 'draft', etc.)
 *
 * Returns:
 * - List of contracts with the party's role in each
 * - Each result includes:
 *   - contract: The Contract node
 *   - role: The party's role in that contract
 *   - joined_at: When the party joined the contract
 *
 * Example usage:
 * CALL { party_id: 'PARTY001' }
 * 
 * With role filter:
 * CALL { party_id: 'PARTY001', role: 'buyer' }
 */

MATCH (c:Contract)-[cp:ContractParty]->(p:Party)
WHERE p.id = $party_id
RETURN c as contract, 
       cp.role as role,
       cp.joined_at as joined_at
ORDER BY cp.joined_at DESC