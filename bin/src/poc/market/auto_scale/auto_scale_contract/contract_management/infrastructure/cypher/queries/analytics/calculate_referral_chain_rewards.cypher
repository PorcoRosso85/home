-- Purpose: Calculate multi-level referral rewards through referral chains
-- Description: Traverses the ReferralChain relationships to calculate
--              commission rates for all parties in the referral network
-- Parameters:
--   $contract_id: STRING - Contract ID that triggered the reward calculation
--   $base_amount: STRING - Base transaction amount (as string for Decimal)
-- Returns:
--   referrer_id: STRING - ID of the party receiving commission
--   referred_id: STRING - ID of the party who made the purchase
--   level: INT64 - Depth in the referral chain (1-5)
--   commission_rate: DOUBLE - Commission rate for this level
--   commission_amount: STRING - Calculated commission amount

MATCH path = (referrer:Party)-[:ReferralChain*1..5]->(buyer:Party)
WHERE exists((buyer)-[:ContractParty {role: 'buyer'}]->(:Contract {id: $contract_id}))
WITH referrer, buyer, length(path) as level
-- Calculate diminishing commission rates: 15% -> 7.5% -> 3.75% -> 1.875% -> 0.9375%
WITH referrer, buyer, level, 
     0.15 * power(0.5, level - 1) as commission_rate
RETURN 
  referrer.id as referrer_id,
  buyer.id as referred_id,
  level,
  commission_rate,
  toString(toFloat($base_amount) * commission_rate) as commission_amount
ORDER BY level ASC