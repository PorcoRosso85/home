/*
 * Create ContractParty Relationship
 * 
 * Creates a relationship between a contract and a party, defining the party's role
 * in the contract (buyer/seller). This relationship includes metadata about the
 * party's participation in the contract.
 *
 * Prerequisites:
 * - Both Contract and Party nodes must exist before creating the relationship
 *
 * Parameters:
 * - $contract_id: ID of the contract
 * - $party_id: ID of the party
 * - $role: Role of the party in the contract ('buyer' or 'seller')
 * - $joined_at: ISO format timestamp when the party joined the contract
 *
 * Optional Parameters:
 * - $commission_rate: Commission rate for the party (if applicable)
 * - $special_terms: Any special terms specific to this party
 *
 * Returns:
 * - The created relationship
 *
 * Example usage:
 * CALL {
 *   contract_id: 'CONTRACT001',
 *   party_id: 'PARTY001',
 *   role: 'buyer',
 *   joined_at: '2024-01-15T10:00:00Z'
 * }
 */

MATCH (c:Contract) WHERE c.id = $contract_id
MATCH (p:Party) WHERE p.id = $party_id
CREATE (c)-[cp:ContractParty {
    role: $role,
    joined_at: $joined_at
}]->(p)
RETURN cp