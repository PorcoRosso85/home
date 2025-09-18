/*
 * Find Referral Chains
 * 
 * Retrieves referral relationships for analysis and commission calculation.
 * Can find referrals by contract, by referrer, or by referred party.
 *
 * Parameters (at least one required):
 * - $contract_id: Find all referrals for a specific contract
 * - $referrer_id: Find all referrals made by a specific party
 * - $referred_id: Find who referred a specific party
 *
 * Returns:
 * - List of referral relationships with party details
 * - Each result includes:
 *   - referrer: The Party node who made the referral
 *   - referred: The Party node who was referred
 *   - referral: The ReferralChain relationship
 *   - contract_id: The associated contract
 *   - commission_rate: The commission rate for this referral
 *
 * Example usage:
 * // Find all referrals for a contract
 * CALL { contract_id: 'CONTRACT001' }
 * 
 * // Find all referrals made by a party
 * CALL { referrer_id: 'PARTY001' }
 * 
 * // Find who referred a specific party
 * CALL { referred_id: 'PARTY003' }
 */

MATCH (referrer:Party)-[r:ReferralChain]->(referred:Party)
WHERE ($contract_id IS NULL OR r.contract_id = $contract_id)
  AND ($referrer_id IS NULL OR referrer.id = $referrer_id)
  AND ($referred_id IS NULL OR referred.id = $referred_id)
RETURN referrer,
       referred,
       r as referral,
       r.contract_id as contract_id,
       r.commission_rate as commission_rate,
       r.referral_date as referral_date
ORDER BY r.referral_date DESC