/*
 * Create Referral Chain Relationship
 * 
 * Creates a referral relationship between two parties for a specific contract.
 * This tracks which party referred another party to a contract opportunity
 * and any associated commission arrangements.
 *
 * Prerequisites:
 * - Both Party nodes must exist before creating the relationship
 *
 * Parameters:
 * - $referrer_id: ID of the party who made the referral
 * - $referred_id: ID of the party who was referred
 * - $contract_id: ID of the contract this referral relates to
 * - $referral_date: ISO format timestamp of when the referral was made
 * - $commission_rate: Commission rate for the referral (0.0 to 1.0)
 *
 * Returns:
 * - The created referral relationship
 *
 * Example usage:
 * CALL {
 *   referrer_id: 'PARTY001',
 *   referred_id: 'PARTY002',
 *   contract_id: 'CONTRACT001',
 *   referral_date: '2024-01-10T09:00:00Z',
 *   commission_rate: 0.05
 * }
 *
 * Note: This relationship is defined in the schema as FROM Party TO Party,
 * representing referrer -> referred direction.
 */

MATCH (referrer:Party) WHERE referrer.id = $referrer_id
MATCH (referred:Party) WHERE referred.id = $referred_id
CREATE (referrer)-[r:ReferralChain {
    contract_id: $contract_id,
    referral_date: $referral_date,
    commission_rate: $commission_rate
}]->(referred)
RETURN r