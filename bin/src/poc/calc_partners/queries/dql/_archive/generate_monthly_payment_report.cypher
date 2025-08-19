// =============================================================================
// Query: Generate Monthly Payment Report
// Purpose: Comprehensive monthly payment report generation with tax and fee calculations
// Pain Point: 「毎月の報酬計算、経理担当がExcelで3日もかけてやってる。ミスも怖い。」
// =============================================================================

// Parameters:
// $reportMonth: INT32 - Month (1-12) for the report
// $reportYear: INT32 - Year for the report
// $partnerId: INT64 (optional) - Specific partner ID (NULL for all partners)
// $minPaymentAmount: DECIMAL (optional, default: 0.01) - Minimum payment threshold
// $taxRate: DECIMAL (optional, default: 0.10) - Tax rate for calculations
// $processingFeeRate: DECIMAL (optional, default: 0.02) - Processing fee rate
// $includeProjections: BOOLEAN (optional, default: false) - Include next month projections
// $exportFormat: STRING (optional, default: 'summary') - 'summary', 'detailed', 'reconciliation'
// $currency: STRING (optional, default: 'JPY') - Currency code for the report

// Validate input parameters
WITH 
  $reportMonth AS report_month,
  $reportYear AS report_year,
  COALESCE($minPaymentAmount, 0.01) AS min_payment,
  COALESCE($taxRate, 0.10) AS tax_rate,
  COALESCE($processingFeeRate, 0.02) AS processing_fee_rate,
  COALESCE($includeProjections, false) AS include_projections,
  COALESCE($exportFormat, 'summary') AS export_format,
  COALESCE($currency, 'JPY') AS currency_code,
  MAKE_DATE(CAST($reportYear AS INT32), CAST($reportMonth AS INT32), 1) AS period_start,
  CASE 
    WHEN $reportMonth = 12 THEN MAKE_DATE(CAST($reportYear + 1 AS INT32), 1, 1) - INTERVAL '1 day'
    ELSE MAKE_DATE(CAST($reportYear AS INT32), CAST($reportMonth + 1 AS INT32), 1) - INTERVAL '1 day'
  END AS period_end

// Get all eligible rewards for the reporting period
MATCH (p:Partner)
WHERE ($partnerId IS NULL OR p.id = $partnerId)

MATCH (r:Reward)
WHERE r.partner_id = p.id
  AND r.status IN ['approved', 'pending']
  AND ((r.period_start >= period_start AND r.period_start <= period_end) OR
       (r.period_end >= period_start AND r.period_end <= period_end) OR
       (r.period_start <= period_start AND r.period_end >= period_end))

OPTIONAL MATCH (r)-[:TRIGGERED_BY]->(t:Transaction)
OPTIONAL MATCH (p)-[:APPLIES_RULE]->(rr:RewardRule)
WHERE r.rule_id = rr.id

// Calculate payment components
WITH p, r, t, rr, period_start, period_end, min_payment, tax_rate, processing_fee_rate, 
     currency_code, export_format, include_projections,
     r.amount AS base_reward_amount,
     r.amount * tax_rate AS tax_amount,
     r.amount * processing_fee_rate AS processing_fee,
     r.amount * (1 - tax_rate - processing_fee_rate) AS net_payment_amount

// Filter by minimum payment threshold
WHERE base_reward_amount >= min_payment

// Aggregate payment data by partner
WITH p, period_start, period_end, currency_code, export_format, include_projections,
     COUNT(r) AS total_rewards,
     SUM(base_reward_amount) AS total_gross_amount,
     SUM(tax_amount) AS total_tax_amount,
     SUM(processing_fee) AS total_processing_fees,
     SUM(net_payment_amount) AS total_net_payment,
     COLLECT(DISTINCT rr.name) AS applied_rules,
     COLLECT(DISTINCT r.status) AS reward_statuses,
     MIN(r.created_at) AS earliest_reward_date,
     MAX(r.created_at) AS latest_reward_date

// Optional: Calculate projections for next month if requested
OPTIONAL MATCH (p)-[:APPLIES_RULE]->(proj_rr:RewardRule)
WHERE include_projections = true
  AND (proj_rr.id IN [rule_id FROM (r2:Reward) WHERE r2.partner_id = p.id])

OPTIONAL MATCH (proj_t:Transaction)
WHERE include_projections = true
  AND proj_t.partner_id = p.id
  AND proj_t.transaction_date >= period_end + INTERVAL '1 day'
  AND proj_t.transaction_date <= period_end + INTERVAL '1 month'
  AND proj_t.status = 'confirmed'

WITH p, period_start, period_end, currency_code, export_format, include_projections,
     total_rewards, total_gross_amount, total_tax_amount, total_processing_fees, total_net_payment,
     applied_rules, reward_statuses, earliest_reward_date, latest_reward_date,
     CASE 
       WHEN include_projections THEN SUM(proj_t.amount * 0.05) -- Estimated 5% commission
       ELSE 0 
     END AS projected_next_month

// Format output based on export format
RETURN 
  // Basic Information
  p.id AS partner_id,
  p.code AS partner_code,
  p.name AS partner_name,
  p.tier AS partner_tier,
  
  // Report Period
  period_start AS report_period_start,
  period_end AS report_period_end,
  CONCAT(CAST(EXTRACT(YEAR FROM period_start) AS STRING), '-', 
         LPAD(CAST(EXTRACT(MONTH FROM period_start) AS STRING), 2, '0')) AS report_period,
  
  // Payment Summary
  total_rewards AS number_of_rewards,
  total_gross_amount AS gross_payment_amount,
  total_tax_amount AS tax_deduction,
  total_processing_fees AS processing_fees,
  total_net_payment AS net_payment_amount,
  currency_code AS currency,
  
  // Payment Details (conditional on export format)
  CASE 
    WHEN export_format IN ['detailed', 'reconciliation'] THEN applied_rules
    ELSE NULL
  END AS applied_reward_rules,
  
  CASE 
    WHEN export_format = 'reconciliation' THEN reward_statuses
    ELSE NULL
  END AS reward_statuses,
  
  CASE 
    WHEN export_format = 'reconciliation' THEN earliest_reward_date
    ELSE NULL
  END AS earliest_reward_date,
  
  CASE 
    WHEN export_format = 'reconciliation' THEN latest_reward_date
    ELSE NULL
  END AS latest_reward_date,
  
  // Projections (if requested)
  CASE 
    WHEN include_projections THEN projected_next_month
    ELSE NULL
  END AS projected_next_month_payment,
  
  // Payment Status
  CASE 
    WHEN total_net_payment > 0 THEN 'payment_due'
    WHEN total_gross_amount > 0 AND total_net_payment <= 0 THEN 'fees_exceed_payment'
    ELSE 'no_payment_due'
  END AS payment_status,
  
  // Metadata
  CURRENT_TIMESTAMP() AS report_generated_at,
  export_format AS report_format,
  
  // Reconciliation Data (for detailed export)
  CASE 
    WHEN export_format = 'reconciliation' THEN
      STRUCT(
        gross_minus_deductions: total_gross_amount - total_tax_amount - total_processing_fees,
        calculated_net: total_net_payment,
        reconciliation_difference: (total_gross_amount - total_tax_amount - total_processing_fees) - total_net_payment,
        validation_status: CASE 
          WHEN ABS((total_gross_amount - total_tax_amount - total_processing_fees) - total_net_payment) < 0.01 
          THEN 'validated' 
          ELSE 'requires_review' 
        END
      )
    ELSE NULL
  END AS reconciliation_data

ORDER BY total_net_payment DESC, p.code ASC

// Usage Examples:
// Basic monthly report: $reportMonth = 8, $reportYear = 2025
// Specific partner: Add $partnerId = 123
// Detailed format: $exportFormat = 'detailed'
// With projections: $includeProjections = true
// Reconciliation: $exportFormat = 'reconciliation'
// Custom tax rate: $taxRate = 0.15