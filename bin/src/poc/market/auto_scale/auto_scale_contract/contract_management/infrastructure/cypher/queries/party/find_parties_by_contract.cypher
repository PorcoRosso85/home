/*
 * Find All Parties Associated with a Contract
 * 
 * Retrieves all parties involved in a specific contract along with their roles
 * and relationship metadata. Used when loading contract details.
 *
 * Parameters:
 * - $contract_id: ID of the contract
 *
 * Returns:
 * - Collection of party nodes with their relationship details
 * - Each result includes:
 *   - party: The Party node
 *   - relationship: The ContractParty relationship with metadata
 *   - role: The party's role in the contract
 *
 * Example usage:
 * CALL { contract_id: 'CONTRACT001' }
 */

MATCH (c:Contract)-[cp:ContractParty]->(p:Party)
WHERE c.id = $contract_id
RETURN p as party, 
       cp as relationship, 
       cp.role as role
ORDER BY cp.role