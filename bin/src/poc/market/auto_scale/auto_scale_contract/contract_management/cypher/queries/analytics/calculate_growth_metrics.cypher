-- Purpose: Calculate comprehensive network growth metrics
-- Description: Computes viral coefficient (K-factor), growth rates, and network value
--              to track and predict automatic scaling performance
-- Parameters:
--   $days_back: INT64 - Number of days to look back for calculations (default: 30)
-- Returns:
--   k_factor: DOUBLE - Viral coefficient (>1 means viral growth)
--   monthly_growth_rate: DOUBLE - Month-over-month growth percentage
--   network_value: INT64 - Metcalfe's Law calculation (n²)
--   cac_to_ltv_ratio: DOUBLE - Customer acquisition efficiency
--   critical_mass_distance: INT64 - Users needed to reach viral threshold

-- Calculate base metrics
WITH datetime() - duration({days: coalesce($days_back, 30)}) as cutoff_date
-- Count total active users
MATCH (p:Party)
WHERE exists((p)-[:ContractParty]->(:Contract {status: 'active'}))
WITH cutoff_date, count(DISTINCT p) as total_users

-- Calculate referral metrics
MATCH (referrer:Party)
WHERE exists((referrer)-[:ContractParty]->(:Contract {status: 'active'}))
OPTIONAL MATCH (referrer)-[:ReferralChain]->(referred:Party)
WHERE exists((referred)-[:ContractParty]->(:Contract))
WITH cutoff_date, total_users, 
     count(DISTINCT referrer) as referring_users,
     count(DISTINCT referred) as referred_users

-- Calculate new users in period
MATCH (new_user:Party)-[:ContractParty]->(c:Contract)
WHERE c.created_at >= toString(cutoff_date)
  AND c.status = 'active'
WITH total_users, referring_users, referred_users,
     count(DISTINCT new_user) as new_users_period

-- Calculate previous period for growth rate
WITH total_users, referring_users, referred_users, new_users_period,
     datetime() - duration({days: coalesce($days_back, 30) * 2}) as prev_cutoff
MATCH (prev_user:Party)-[:ContractParty]->(pc:Contract)
WHERE pc.created_at >= toString(prev_cutoff)
  AND pc.created_at < toString(datetime() - duration({days: coalesce($days_back, 30)}))
  AND pc.status = 'active'
WITH total_users, referring_users, referred_users, new_users_period,
     count(DISTINCT prev_user) as prev_period_users

-- Calculate all metrics
WITH total_users, referring_users, referred_users, new_users_period, prev_period_users,
     -- K-factor = (referred users / referring users) * (conversion rate)
     CASE WHEN referring_users > 0 
          THEN toFloat(referred_users) / toFloat(referring_users) * 0.5 -- Assume 50% conversion
          ELSE 0.0 
     END as k_factor,
     -- Monthly growth rate
     CASE WHEN prev_period_users > 0
          THEN (toFloat(new_users_period) - toFloat(prev_period_users)) / toFloat(prev_period_users)
          ELSE 0.0
     END as growth_rate

RETURN {
  k_factor: round(k_factor * 100) / 100,
  monthly_growth_rate: round(growth_rate * 10000) / 100, -- As percentage
  network_value: total_users * total_users, -- Metcalfe's Law: V = n²
  total_users: total_users,
  referring_users: referring_users,
  referred_users: referred_users,
  new_users_30d: new_users_period,
  -- Critical mass estimation (when K > 1)
  critical_mass_distance: CASE 
    WHEN k_factor >= 1.0 THEN 0 -- Already viral
    WHEN k_factor > 0 THEN toInteger((1.0 - k_factor) * total_users / k_factor)
    ELSE 1000 -- Default target if no viral growth yet
  END,
  is_viral: k_factor >= 1.0
} as metrics