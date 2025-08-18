// =============================================================================
// Query: Calculate LTV (Lifetime Value)
// Purpose: Calculate Customer/Partner Lifetime Value based on transaction history and projections
// =============================================================================

// Parameters:
// $partnerId: INT64 (optional) - Specific partner ID to calculate LTV for
// $projectionMonths: INT32 (optional, default: 12) - Number of months to project forward
// $includeChurnPrediction: BOOLEAN (optional, default: true) - Include churn probability in calculation
// $segmentByTier: BOOLEAN (optional, default: false) - Segment results by partner tier
// $analysisDate: DATE (optional, default: current date) - Reference date for LTV calculation

// Set default values
WITH COALESCE($projectionMonths, 12) AS projection_months,
     COALESCE($includeChurnPrediction, true) AS include_churn,
     COALESCE($segmentByTier, false) AS segment_by_tier,
     COALESCE($analysisDate, CURRENT_DATE()) AS analysis_date

// Get partners to analyze
OPTIONAL MATCH (p:Partner {id: $partnerId})
WHERE $partnerId IS NOT NULL

OPTIONAL MATCH (all_partners:Partner)
WHERE $partnerId IS NULL

WITH projection_months, include_churn, segment_by_tier, analysis_date,
  CASE 
    WHEN $partnerId IS NOT NULL THEN COLLECT(p)
    ELSE COLLECT(all_partners)
  END AS partners_to_analyze

UNWIND partners_to_analyze AS partner

// Get all historical transactions for the partner
MATCH (transactions:Transaction {partner_id: partner.id})
WHERE transactions.status = 'confirmed'
  AND transactions.transaction_date <= analysis_date

// Calculate partner age and activity metrics
WITH partner, transactions, projection_months, include_churn, segment_by_tier, analysis_date,
  MIN(transactions.transaction_date) AS first_transaction_date,
  MAX(transactions.transaction_date) AS last_transaction_date,
  COUNT(transactions.id) AS total_transactions,
  SUM(transactions.amount) AS total_revenue,
  AVG(transactions.amount) AS avg_transaction_value

// Calculate time-based metrics
WITH partner, projection_months, include_churn, segment_by_tier, analysis_date,
  first_transaction_date, last_transaction_date, total_transactions, total_revenue, avg_transaction_value,
  DURATION.BETWEEN(first_transaction_date, analysis_date).days AS customer_age_days,
  DURATION.BETWEEN(last_transaction_date, analysis_date).days AS days_since_last_transaction,
  DURATION.BETWEEN(first_transaction_date, last_transaction_date).days AS active_period_days

// Calculate monthly and frequency metrics
WITH partner, projection_months, include_churn, segment_by_tier, analysis_date,
  first_transaction_date, last_transaction_date, total_transactions, total_revenue, avg_transaction_value,
  customer_age_days, days_since_last_transaction, active_period_days,
  CASE 
    WHEN customer_age_days > 0 THEN customer_age_days / 30.0
    ELSE 1
  END AS customer_age_months,
  CASE 
    WHEN active_period_days > 0 THEN total_transactions / (active_period_days / 30.0)
    ELSE total_transactions
  END AS avg_transactions_per_month,
  CASE 
    WHEN customer_age_days > 0 THEN total_revenue / (customer_age_days / 30.0)
    ELSE total_revenue
  END AS avg_monthly_revenue

// Calculate churn probability (simple model based on recency)
WITH partner, projection_months, include_churn, segment_by_tier, analysis_date,
  first_transaction_date, last_transaction_date, total_transactions, total_revenue, avg_transaction_value,
  customer_age_days, days_since_last_transaction, active_period_days,
  customer_age_months, avg_transactions_per_month, avg_monthly_revenue,
  CASE 
    WHEN days_since_last_transaction <= 30 THEN 0.05
    WHEN days_since_last_transaction <= 60 THEN 0.15
    WHEN days_since_last_transaction <= 90 THEN 0.30
    WHEN days_since_last_transaction <= 180 THEN 0.50
    WHEN days_since_last_transaction <= 365 THEN 0.75
    ELSE 0.90
  END AS churn_probability

// Calculate projected LTV
WITH partner, projection_months, include_churn, segment_by_tier, analysis_date,
  first_transaction_date, last_transaction_date, total_transactions, total_revenue, avg_transaction_value,
  customer_age_days, days_since_last_transaction, customer_age_months, 
  avg_transactions_per_month, avg_monthly_revenue, churn_probability,
  // Base LTV calculation
  avg_monthly_revenue * projection_months AS base_projected_ltv,
  // Churn-adjusted LTV calculation
  CASE 
    WHEN include_churn THEN avg_monthly_revenue * projection_months * (1 - churn_probability)
    ELSE avg_monthly_revenue * projection_months
  END AS churn_adjusted_ltv

// Get network value if partner has referrals
OPTIONAL MATCH (partner)-[:REFERS]->(referred:Partner)
OPTIONAL MATCH (ref_transactions:Transaction {partner_id: referred.id})
WHERE ref_transactions.status = 'confirmed'
  AND ref_transactions.transaction_date <= analysis_date

WITH partner, projection_months, include_churn, segment_by_tier, analysis_date,
  first_transaction_date, last_transaction_date, total_transactions, total_revenue, avg_transaction_value,
  customer_age_days, days_since_last_transaction, customer_age_months,
  avg_transactions_per_month, avg_monthly_revenue, churn_probability,
  base_projected_ltv, churn_adjusted_ltv,
  COUNT(DISTINCT referred.id) AS referred_partners_count,
  COALESCE(SUM(ref_transactions.amount), 0) AS network_revenue,
  CASE 
    WHEN COUNT(DISTINCT referred.id) > 0 THEN COALESCE(SUM(ref_transactions.amount), 0) * 0.1
    ELSE 0
  END AS network_value_bonus

// Calculate final LTV with network effects
WITH partner, projection_months, include_churn, segment_by_tier, analysis_date,
  first_transaction_date, last_transaction_date, total_transactions, total_revenue, avg_transaction_value,
  customer_age_days, days_since_last_transaction, customer_age_months,
  avg_transactions_per_month, avg_monthly_revenue, churn_probability,
  base_projected_ltv, churn_adjusted_ltv, referred_partners_count, network_revenue, network_value_bonus,
  churn_adjusted_ltv + network_value_bonus AS total_ltv

RETURN 
  partner.id AS partner_id,
  partner.code AS partner_code,
  partner.name AS partner_name,
  partner.tier AS partner_tier,
  first_transaction_date AS first_transaction_date,
  last_transaction_date AS last_transaction_date,
  ROUND(customer_age_months, 2) AS customer_age_months,
  days_since_last_transaction AS days_since_last_transaction,
  total_transactions AS total_transactions,
  total_revenue AS historical_total_revenue,
  ROUND(avg_transaction_value, 2) AS avg_transaction_value,
  ROUND(avg_transactions_per_month, 2) AS avg_transactions_per_month,
  ROUND(avg_monthly_revenue, 2) AS avg_monthly_revenue,
  ROUND(churn_probability * 100, 2) AS churn_probability_percentage,
  ROUND(base_projected_ltv, 2) AS base_projected_ltv,
  ROUND(churn_adjusted_ltv, 2) AS churn_adjusted_ltv,
  referred_partners_count AS network_referrals,
  network_revenue AS network_generated_revenue,
  ROUND(network_value_bonus, 2) AS network_value_bonus,
  ROUND(total_ltv, 2) AS total_lifetime_value,
  projection_months AS projection_period_months,
  CASE 
    WHEN total_ltv >= 10000 THEN 'high_value'
    WHEN total_ltv >= 5000 THEN 'medium_value'
    WHEN total_ltv >= 1000 THEN 'low_value'
    ELSE 'minimal_value'
  END AS ltv_segment,
  CASE 
    WHEN churn_probability <= 0.2 THEN 'low_risk'
    WHEN churn_probability <= 0.5 THEN 'medium_risk'
    ELSE 'high_risk'
  END AS churn_risk_category,
  analysis_date AS analysis_date

ORDER BY total_lifetime_value DESC;