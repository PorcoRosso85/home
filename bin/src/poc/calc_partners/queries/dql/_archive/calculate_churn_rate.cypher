// =============================================================================
// Query: Calculate Churn Rate
// Purpose: Calculate partner/customer churn rate based on transaction activity
// Pain Point: Track partner retention and identify at-risk relationships
// =============================================================================
//
// Parameters:
// - $periodStartDate: Start date of the evaluation period (DATE, e.g., '2024-01-01')
// - $periodEndDate: End date of the evaluation period (DATE, e.g., '2024-03-31')
// - $lookbackMonths: Number of months to look back for activity (INT32, e.g., 3)
// - $partnerTier: Optional - Calculate churn for specific tier (STRING, null for all)
// - $inactivityThreshold: Days without transaction to consider churned (INT32, e.g., 90)
//
// Returns:
// - period_start: Start of evaluation period
// - period_end: End of evaluation period
// - tier: Partner tier (or 'ALL' for overall)
// - total_partners: Total partners at start of period
// - active_partners: Partners with transactions in period
// - churned_partners: Partners without transactions in period
// - churn_rate: Percentage of partners that churned
// - avg_days_since_last_transaction: Average days since last transaction for churned partners
// - retention_rate: Percentage of partners retained (100 - churn_rate)
//
// =============================================================================

// First, get all partners that existed at the start of the period
MATCH (p:Partner)
WHERE p.created_at <= TIMESTAMP($periodStartDate)
  AND ($partnerTier IS NULL OR p.tier = $partnerTier)

WITH p, 
     $periodStartDate AS period_start,
     $periodEndDate AS period_end,
     COALESCE($partnerTier, 'ALL') AS evaluation_tier

// Find their last transaction before or during the period
OPTIONAL MATCH (p)-[:TRIGGERED_BY]-(r:Reward)-[:TRIGGERED_BY]-(t:Transaction)
WHERE t.transaction_date <= DATE($periodEndDate)
  AND t.status = 'confirmed'

WITH p, period_start, period_end, evaluation_tier,
     MAX(t.transaction_date) AS last_transaction_date,
     COUNT(DISTINCT t) AS transaction_count

// Calculate days since last transaction
WITH p, period_start, period_end, evaluation_tier, last_transaction_date,
     transaction_count,
     CASE 
       WHEN last_transaction_date IS NULL 
       THEN 999999  // Never had a transaction
       ELSE DATE_DIFF('day', last_transaction_date, DATE($periodEndDate))
     END AS days_since_last_transaction

// Classify partners as active or churned
WITH evaluation_tier, period_start, period_end,
     COUNT(p) AS total_partners,
     SUM(CASE 
       WHEN days_since_last_transaction <= $inactivityThreshold 
       THEN 1 
       ELSE 0 
     END) AS active_partners,
     SUM(CASE 
       WHEN days_since_last_transaction > $inactivityThreshold 
       THEN 1 
       ELSE 0 
     END) AS churned_partners,
     AVG(CASE 
       WHEN days_since_last_transaction > $inactivityThreshold 
       THEN days_since_last_transaction 
       ELSE NULL 
     END) AS avg_days_since_last_transaction

RETURN 
  period_start,
  period_end,
  evaluation_tier AS tier,
  total_partners,
  active_partners,
  churned_partners,
  CASE 
    WHEN total_partners > 0 
    THEN ROUND((churned_partners * 100.0 / total_partners), 2)
    ELSE 0.0
  END AS churn_rate,
  CASE 
    WHEN avg_days_since_last_transaction IS NOT NULL
    THEN ROUND(avg_days_since_last_transaction, 1)
    ELSE NULL
  END AS avg_days_since_last_transaction,
  CASE 
    WHEN total_partners > 0 
    THEN ROUND((active_partners * 100.0 / total_partners), 2)
    ELSE 0.0
  END AS retention_rate

ORDER BY tier;

// =============================================================================
// Alternative Query: Detailed Churn Analysis by Partner
// =============================================================================
/*
MATCH (p:Partner)
WHERE p.created_at <= TIMESTAMP($periodStartDate)
  AND ($partnerTier IS NULL OR p.tier = $partnerTier)

OPTIONAL MATCH (p)-[:TRIGGERED_BY]-(r:Reward)-[:TRIGGERED_BY]-(t:Transaction)
WHERE t.transaction_date <= DATE($periodEndDate)
  AND t.status = 'confirmed'

WITH p,
     MAX(t.transaction_date) AS last_transaction_date,
     COUNT(DISTINCT t) AS total_transactions,
     SUM(t.amount) AS total_transaction_value

WITH p, last_transaction_date, total_transactions, total_transaction_value,
     CASE 
       WHEN last_transaction_date IS NULL 
       THEN 999999
       ELSE DATE_DIFF('day', last_transaction_date, DATE($periodEndDate))
     END AS days_since_last_transaction,
     CASE 
       WHEN last_transaction_date IS NULL 
       THEN 'NEVER_ACTIVE'
       WHEN DATE_DIFF('day', last_transaction_date, DATE($periodEndDate)) <= $inactivityThreshold
       THEN 'ACTIVE'
       ELSE 'CHURNED'
     END AS status

RETURN 
  p.id AS partner_id,
  p.name AS partner_name,
  p.tier AS tier,
  p.created_at AS created_date,
  last_transaction_date,
  days_since_last_transaction,
  total_transactions,
  total_transaction_value,
  status

ORDER BY days_since_last_transaction DESC, total_transaction_value DESC;
*/

// =============================================================================
// Example Usage:
// 
// 1. Calculate quarterly churn rate with 90-day inactivity threshold:
// {
//   "periodStartDate": "2024-01-01",
//   "periodEndDate": "2024-03-31",
//   "lookbackMonths": 3,
//   "partnerTier": null,
//   "inactivityThreshold": 90
// }
//
// 2. Calculate churn rate for premium partners only:
// {
//   "periodStartDate": "2024-01-01",
//   "periodEndDate": "2024-03-31",
//   "lookbackMonths": 6,
//   "partnerTier": "premium",
//   "inactivityThreshold": 60
// }
//
// 3. Monthly churn analysis with strict 30-day threshold:
// {
//   "periodStartDate": "2024-03-01",
//   "periodEndDate": "2024-03-31",
//   "lookbackMonths": 1,
//   "partnerTier": null,
//   "inactivityThreshold": 30
// }
// =============================================================================