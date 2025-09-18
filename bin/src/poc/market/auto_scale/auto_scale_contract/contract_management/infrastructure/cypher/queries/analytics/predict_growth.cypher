-- Purpose: Predict future network growth based on current metrics
-- Description: Uses historical growth patterns and viral coefficient to
--              project future user counts and revenue
-- Parameters:
--   $days_ahead: INT64 - Number of days to predict ahead (default: 90)
-- Returns:
--   prediction_date: STRING - Date of prediction
--   predicted_users: INT64 - Estimated user count
--   predicted_revenue: STRING - Estimated total contract value
--   confidence_level: STRING - HIGH/MEDIUM/LOW based on data quality

-- Get current metrics and historical growth
WITH datetime() as current_date,
     coalesce($days_ahead, 90) as prediction_days

-- Calculate average daily growth rate from last 90 days
MATCH (p:Party)-[:ContractParty]->(c:Contract)
WHERE c.created_at >= toString(current_date - duration({days: 90}))
  AND c.status = 'active'
WITH current_date, prediction_days,
     count(DISTINCT p) as recent_users,
     90.0 as period_days

-- Get total current users
MATCH (all_p:Party)
WHERE exists((all_p)-[:ContractParty]->(:Contract {status: 'active'}))
WITH current_date, prediction_days, recent_users, period_days,
     count(DISTINCT all_p) as current_users

-- Calculate K-factor for viral growth modeling
MATCH (referrer:Party)
WHERE exists((referrer)-[:ContractParty]->(:Contract {status: 'active'}))
OPTIONAL MATCH (referrer)-[:ReferralChain]->(referred:Party)
WHERE exists((referred)-[:ContractParty]->(:Contract {status: 'active'}))
WITH current_date, prediction_days, recent_users, period_days, current_users,
     count(DISTINCT referrer) as referring_users,
     count(DISTINCT referred) as referred_users

-- Calculate growth parameters
WITH current_date, prediction_days, current_users,
     recent_users / period_days as daily_growth_rate,
     CASE WHEN referring_users > 0 
          THEN toFloat(referred_users) / toFloat(referring_users) * 0.5
          ELSE 0.0 
     END as k_factor

-- Project future growth using compound growth formula
-- If K > 1 (viral), use exponential model: N(t) = N0 * K^t
-- If K < 1, use linear model: N(t) = N0 + (growth_rate * t)
WITH current_date, prediction_days, current_users, daily_growth_rate, k_factor,
     CASE
       WHEN k_factor >= 1.0 THEN 
         -- Exponential growth with dampening factor
         toInteger(current_users * power(k_factor, prediction_days / 30.0))
       ELSE 
         -- Linear growth projection
         toInteger(current_users + (daily_growth_rate * prediction_days))
     END as predicted_users

-- Calculate average contract value for revenue projection
MATCH (c:Contract)
WHERE c.status = 'active' AND c.value_amount IS NOT NULL
WITH current_date, prediction_days, current_users, predicted_users, k_factor,
     avg(toFloat(c.value_amount)) as avg_contract_value

-- Determine confidence level based on data quality and growth stability
WITH current_date, prediction_days, current_users, predicted_users, 
     k_factor, avg_contract_value,
     CASE
       WHEN current_users < 10 THEN 'LOW'
       WHEN k_factor >= 0.8 AND current_users >= 100 THEN 'HIGH'
       WHEN k_factor >= 0.5 AND current_users >= 50 THEN 'MEDIUM'
       ELSE 'LOW'
     END as confidence_level

RETURN {
  current_date: toString(current_date),
  prediction_date: toString(current_date + duration({days: prediction_days})),
  current_users: current_users,
  predicted_users: predicted_users,
  growth_multiplier: round(toFloat(predicted_users) / toFloat(current_users) * 100) / 100,
  predicted_revenue: toString(predicted_users * avg_contract_value),
  k_factor: round(k_factor * 100) / 100,
  confidence_level: confidence_level,
  growth_type: CASE WHEN k_factor >= 1.0 THEN 'VIRAL' ELSE 'LINEAR' END
} as prediction