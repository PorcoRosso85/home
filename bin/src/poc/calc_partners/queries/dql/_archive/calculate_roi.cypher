// =============================================================================
// Query: Calculate ROI (Return on Investment)
// Purpose: Calculate Return on Investment for partners based on rewards paid vs revenue generated
// =============================================================================

// Parameters:
// $partnerId: INT64 (optional) - Specific partner ID to calculate ROI for
// $periodStart: DATE - Start date for ROI calculation period
// $periodEnd: DATE - End date for ROI calculation period
// $investmentAmount: DECIMAL(15,2) (optional) - Override investment amount if provided
// $includeNetworkROI: BOOLEAN (optional, default: false) - Include network/referral ROI

// If partnerId is provided, calculate for specific partner, otherwise for all partners
OPTIONAL MATCH (p:Partner {id: $partnerId})
WHERE $partnerId IS NOT NULL

OPTIONAL MATCH (all_partners:Partner)
WHERE $partnerId IS NULL

WITH CASE 
  WHEN $partnerId IS NOT NULL THEN COLLECT(p)
  ELSE COLLECT(all_partners)
END AS partners_to_analyze

UNWIND partners_to_analyze AS partner

// Get all transactions for the partner in the period
MATCH (transactions:Transaction {partner_id: partner.id})
WHERE transactions.transaction_date >= $periodStart
  AND transactions.transaction_date <= $periodEnd
  AND transactions.status = 'confirmed'

// Get all rewards paid to the partner in the period
MATCH (rewards:Reward {partner_id: partner.id})
WHERE rewards.period_start >= $periodStart
  AND rewards.period_end <= $periodEnd
  AND rewards.status IN ['approved', 'paid']

// Calculate network revenue if requested
OPTIONAL MATCH (partner)-[ref:REFERS]->(referred_partners:Partner)
WHERE $includeNetworkROI = true
OPTIONAL MATCH (network_transactions:Transaction {partner_id: referred_partners.id})
WHERE network_transactions.transaction_date >= $periodStart
  AND network_transactions.transaction_date <= $periodEnd
  AND network_transactions.status = 'confirmed'

// Calculate network rewards if requested
OPTIONAL MATCH (network_rewards:Reward {partner_id: referred_partners.id})
WHERE $includeNetworkROI = true
  AND network_rewards.period_start >= $periodStart
  AND network_rewards.period_end <= $periodEnd
  AND network_rewards.status IN ['approved', 'paid']

// Aggregate all metrics
WITH partner,
  SUM(transactions.amount) AS total_revenue_generated,
  COUNT(transactions.id) AS total_transactions,
  SUM(rewards.amount) AS total_rewards_paid,
  COUNT(rewards.id) AS total_rewards_count,
  COALESCE(SUM(network_transactions.amount), 0) AS network_revenue_generated,
  COALESCE(COUNT(network_transactions.id), 0) AS network_transactions_count,
  COALESCE(SUM(network_rewards.amount), 0) AS network_rewards_paid,
  COUNT(DISTINCT referred_partners.id) AS referred_partners_count

// Calculate investment amount (rewards paid are the investment)
WITH partner, total_revenue_generated, total_transactions, total_rewards_paid, total_rewards_count,
  network_revenue_generated, network_transactions_count, network_rewards_paid, referred_partners_count,
  CASE 
    WHEN $investmentAmount IS NOT NULL THEN $investmentAmount
    ELSE total_rewards_paid + network_rewards_paid
  END AS investment_amount

// Calculate ROI metrics
WITH partner, total_revenue_generated, total_transactions, total_rewards_paid, total_rewards_count,
  network_revenue_generated, network_transactions_count, network_rewards_paid, referred_partners_count,
  investment_amount,
  total_revenue_generated + network_revenue_generated AS total_returns,
  total_revenue_generated - total_rewards_paid AS net_profit,
  (total_revenue_generated + network_revenue_generated) - (total_rewards_paid + network_rewards_paid) AS total_net_profit

// Calculate ROI percentages
WITH partner, total_revenue_generated, total_transactions, total_rewards_paid, total_rewards_count,
  network_revenue_generated, network_transactions_count, network_rewards_paid, referred_partners_count,
  investment_amount, total_returns, net_profit, total_net_profit,
  CASE 
    WHEN investment_amount > 0 THEN (total_returns - investment_amount) / investment_amount * 100
    ELSE 0
  END AS roi_percentage,
  CASE 
    WHEN total_rewards_paid > 0 THEN total_revenue_generated / total_rewards_paid
    ELSE 0
  END AS revenue_multiplier,
  CASE 
    WHEN total_revenue_generated > 0 THEN total_rewards_paid / total_revenue_generated * 100
    ELSE 0
  END AS reward_cost_percentage

RETURN 
  partner.id AS partner_id,
  partner.code AS partner_code,
  partner.name AS partner_name,
  partner.tier AS partner_tier,
  total_revenue_generated AS revenue_generated,
  total_transactions AS transaction_count,
  total_rewards_paid AS investment_rewards_paid,
  total_rewards_count AS rewards_count,
  network_revenue_generated AS network_revenue,
  network_rewards_paid AS network_investment,
  referred_partners_count AS network_size,
  investment_amount AS total_investment,
  total_returns AS total_returns,
  net_profit AS direct_net_profit,
  total_net_profit AS total_net_profit,
  roi_percentage AS roi_percentage,
  revenue_multiplier AS revenue_multiplier,
  reward_cost_percentage AS reward_cost_percentage,
  CASE 
    WHEN roi_percentage >= 200 THEN 'excellent'
    WHEN roi_percentage >= 100 THEN 'good'
    WHEN roi_percentage >= 50 THEN 'fair'
    WHEN roi_percentage >= 0 THEN 'poor'
    ELSE 'negative'
  END AS roi_rating,
  $periodStart AS period_start,
  $periodEnd AS period_end

ORDER BY roi_percentage DESC;