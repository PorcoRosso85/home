// =============================================================================
// Query: Analyze Revenue Sensitivity
// Purpose: What-if analysis for strategic planning and risk management
// Pain Point: "How would changes in our reward structure or partner behavior affect our revenue?"
// =============================================================================
//
// Parameters:
// $baseStartDate: Base period start date (format: 'YYYY-MM-DD')
// $baseEndDate: Base period end date (format: 'YYYY-MM-DD')
// $rewardRateAdjustment: Percentage change in reward rates (+/- percentage, e.g., 10 for +10%)
// $partnerVolumeChange: Percentage change in partner transaction volume (+/- percentage)
// $newPartnerCount: Number of new partners to simulate
// $churnRate: Percentage of partners expected to churn (0-100)
// $scenarioName: Name for this sensitivity analysis scenario
//
// Business Metrics Provided:
// - Revenue impact modeling under different scenarios
// - Break-even analysis for reward structure changes
// - Risk assessment for partner portfolio changes
// - Optimization recommendations based on sensitivity analysis
// - ROI projections for different strategic initiatives

// Get baseline performance data
MATCH (p:Partner)
OPTIONAL MATCH (p)-[:APPLIES_RULE]-(rule:RewardRule)
OPTIONAL MATCH (t:Transaction)-[:TRIGGERED_BY]-(r:Reward)
WHERE t.partner_id = p.id
  AND t.transaction_date >= date($baseStartDate) 
  AND t.transaction_date <= date($baseEndDate)
  AND t.status = 'confirmed'

// Calculate baseline metrics by partner tier
WITH p.tier AS tier,
  count(DISTINCT p.id) AS partner_count,
  count(t.id) AS transaction_count,
  sum(t.amount) AS total_revenue,
  sum(r.amount) AS total_rewards,
  avg(t.amount) AS avg_transaction_size,
  avg(r.amount) AS avg_reward_per_transaction,
  rule.type AS rule_type

WITH tier, partner_count, transaction_count, total_revenue, total_rewards, 
     avg_transaction_size, avg_reward_per_transaction, rule_type,
     (total_revenue - total_rewards) AS baseline_net_revenue,
     CASE WHEN total_revenue > 0 THEN (total_rewards / total_revenue) * 100 ELSE 0 END AS baseline_reward_rate

// Calculate baseline summary
WITH COLLECT({
  tier: tier,
  partner_count: partner_count,
  transaction_count: transaction_count,
  total_revenue: total_revenue,
  total_rewards: total_rewards,
  baseline_net_revenue: baseline_net_revenue,
  baseline_reward_rate: baseline_reward_rate,
  avg_transaction_size: avg_transaction_size,
  avg_reward_per_transaction: avg_reward_per_transaction,
  rule_type: rule_type
}) AS baseline_data

// Scenario 1: Reward Rate Adjustment
UNWIND baseline_data AS baseline
WITH baseline_data, baseline,
  baseline.total_revenue * (1 + COALESCE($partnerVolumeChange, 0) / 100) AS adjusted_revenue,
  baseline.avg_reward_per_transaction * (1 + COALESCE($rewardRateAdjustment, 0) / 100) AS adjusted_reward_per_transaction

WITH baseline_data, baseline, adjusted_revenue, adjusted_reward_per_transaction,
  adjusted_revenue * (baseline.total_rewards / baseline.total_revenue) * 
  (1 + COALESCE($rewardRateAdjustment, 0) / 100) AS adjusted_total_rewards

WITH baseline_data,
  COLLECT({
    tier: baseline.tier,
    scenario: 'reward_rate_adjustment',
    original_revenue: baseline.total_revenue,
    projected_revenue: adjusted_revenue,
    original_rewards: baseline.total_rewards,
    projected_rewards: adjusted_total_rewards,
    original_net: baseline.baseline_net_revenue,
    projected_net: adjusted_revenue - adjusted_total_rewards,
    revenue_change: adjusted_revenue - baseline.total_revenue,
    reward_change: adjusted_total_rewards - baseline.total_rewards,
    net_change: (adjusted_revenue - adjusted_total_rewards) - baseline.baseline_net_revenue,
    impact_percent: CASE 
      WHEN baseline.baseline_net_revenue != 0 
      THEN ((adjusted_revenue - adjusted_total_rewards) - baseline.baseline_net_revenue) / baseline.baseline_net_revenue * 100
      ELSE NULL 
    END
  }) AS reward_adjustment_scenario

// Scenario 2: Partner Volume Change
UNWIND baseline_data AS baseline
WITH baseline_data, reward_adjustment_scenario, baseline,
  baseline.transaction_count * (1 + COALESCE($partnerVolumeChange, 0) / 100) AS volume_adjusted_transactions,
  baseline.total_revenue * (1 + COALESCE($partnerVolumeChange, 0) / 100) AS volume_adjusted_revenue

WITH baseline_data, reward_adjustment_scenario, baseline, volume_adjusted_transactions, volume_adjusted_revenue,
  volume_adjusted_revenue * (baseline.baseline_reward_rate / 100) AS volume_adjusted_rewards

WITH baseline_data, reward_adjustment_scenario,
  COLLECT({
    tier: baseline.tier,
    scenario: 'volume_change',
    original_revenue: baseline.total_revenue,
    projected_revenue: volume_adjusted_revenue,
    original_rewards: baseline.total_rewards,
    projected_rewards: volume_adjusted_rewards,
    original_net: baseline.baseline_net_revenue,
    projected_net: volume_adjusted_revenue - volume_adjusted_rewards,
    revenue_change: volume_adjusted_revenue - baseline.total_revenue,
    reward_change: volume_adjusted_rewards - baseline.total_rewards,
    net_change: (volume_adjusted_revenue - volume_adjusted_rewards) - baseline.baseline_net_revenue,
    transaction_change: volume_adjusted_transactions - baseline.transaction_count,
    impact_percent: CASE 
      WHEN baseline.baseline_net_revenue != 0 
      THEN ((volume_adjusted_revenue - volume_adjusted_rewards) - baseline.baseline_net_revenue) / baseline.baseline_net_revenue * 100
      ELSE NULL 
    END
  }) AS volume_change_scenario

// Scenario 3: New Partner Acquisition
UNWIND baseline_data AS baseline
WITH baseline_data, reward_adjustment_scenario, volume_change_scenario, baseline,
  // Assume new partners perform at 70% of tier average initially
  COALESCE($newPartnerCount, 0) * (baseline.total_revenue / baseline.partner_count) * 0.7 AS new_partner_revenue,
  COALESCE($newPartnerCount, 0) * (baseline.total_rewards / baseline.partner_count) * 0.7 AS new_partner_rewards

WITH baseline_data, reward_adjustment_scenario, volume_change_scenario,
  COLLECT({
    tier: baseline.tier,
    scenario: 'new_partner_acquisition',
    original_revenue: baseline.total_revenue,
    projected_revenue: baseline.total_revenue + new_partner_revenue,
    original_rewards: baseline.total_rewards,
    projected_rewards: baseline.total_rewards + new_partner_rewards,
    original_net: baseline.baseline_net_revenue,
    projected_net: baseline.baseline_net_revenue + (new_partner_revenue - new_partner_rewards),
    revenue_change: new_partner_revenue,
    reward_change: new_partner_rewards,
    net_change: new_partner_revenue - new_partner_rewards,
    new_partners_added: COALESCE($newPartnerCount, 0),
    impact_percent: CASE 
      WHEN baseline.baseline_net_revenue != 0 
      THEN (new_partner_revenue - new_partner_rewards) / baseline.baseline_net_revenue * 100
      ELSE NULL 
    END
  }) AS new_partner_scenario

// Scenario 4: Partner Churn Impact
UNWIND baseline_data AS baseline
WITH baseline_data, reward_adjustment_scenario, volume_change_scenario, new_partner_scenario, baseline,
  baseline.total_revenue * (COALESCE($churnRate, 0) / 100) AS churn_revenue_loss,
  baseline.total_rewards * (COALESCE($churnRate, 0) / 100) AS churn_reward_savings

WITH baseline_data, reward_adjustment_scenario, volume_change_scenario, new_partner_scenario,
  COLLECT({
    tier: baseline.tier,
    scenario: 'partner_churn',
    original_revenue: baseline.total_revenue,
    projected_revenue: baseline.total_revenue - churn_revenue_loss,
    original_rewards: baseline.total_rewards,
    projected_rewards: baseline.total_rewards - churn_reward_savings,
    original_net: baseline.baseline_net_revenue,
    projected_net: baseline.baseline_net_revenue - (churn_revenue_loss - churn_reward_savings),
    revenue_change: -churn_revenue_loss,
    reward_change: -churn_reward_savings,
    net_change: -(churn_revenue_loss - churn_reward_savings),
    partners_lost: round(baseline.partner_count * (COALESCE($churnRate, 0) / 100)),
    impact_percent: CASE 
      WHEN baseline.baseline_net_revenue != 0 
      THEN -(churn_revenue_loss - churn_reward_savings) / baseline.baseline_net_revenue * 100
      ELSE NULL 
    END
  }) AS churn_scenario

// Combined scenario analysis
WITH baseline_data, reward_adjustment_scenario, volume_change_scenario, new_partner_scenario, churn_scenario,
  reduce(sum = 0, item IN baseline_data | sum + item.total_revenue) AS total_baseline_revenue,
  reduce(sum = 0, item IN baseline_data | sum + item.total_rewards) AS total_baseline_rewards,
  reduce(sum = 0, item IN baseline_data | sum + item.baseline_net_revenue) AS total_baseline_net

// Calculate break-even points
WITH baseline_data, reward_adjustment_scenario, volume_change_scenario, new_partner_scenario, churn_scenario,
  total_baseline_revenue, total_baseline_rewards, total_baseline_net,
  
  // Break-even reward rate increase (what volume increase offsets reward rate increase)
  CASE 
    WHEN COALESCE($rewardRateAdjustment, 0) > 0
    THEN COALESCE($rewardRateAdjustment, 0)  // Same percentage volume increase needed
    ELSE NULL 
  END AS breakeven_volume_increase_needed,
  
  // Break-even analysis for new partner acquisition
  CASE 
    WHEN COALESCE($newPartnerCount, 0) > 0 AND total_baseline_net > 0
    THEN (total_baseline_net * 0.1) / COALESCE($newPartnerCount, 1)  // Revenue per new partner needed for 10% net increase
    ELSE NULL 
  END AS revenue_per_new_partner_needed

RETURN {
  analysis_metadata: {
    scenario_name: COALESCE($scenarioName, 'sensitivity_analysis'),
    base_period: $baseStartDate + ' to ' + $baseEndDate,
    parameters: {
      reward_rate_adjustment: COALESCE($rewardRateAdjustment, 0),
      partner_volume_change: COALESCE($partnerVolumeChange, 0),
      new_partner_count: COALESCE($newPartnerCount, 0),
      churn_rate: COALESCE($churnRate, 0)
    }
  },
  baseline_summary: {
    total_revenue: total_baseline_revenue,
    total_rewards: total_baseline_rewards,
    total_net_revenue: total_baseline_net,
    baseline_reward_rate: (total_baseline_rewards / total_baseline_revenue) * 100,
    tier_breakdown: baseline_data
  },
  scenario_analysis: {
    reward_rate_adjustment: {
      description: 'Impact of changing reward rates by ' + toString(COALESCE($rewardRateAdjustment, 0)) + '%',
      total_impact: reduce(sum = 0, item IN reward_adjustment_scenario | sum + item.net_change),
      impact_percent: reduce(sum = 0, item IN reward_adjustment_scenario | sum + item.net_change) / total_baseline_net * 100,
      tier_details: reward_adjustment_scenario
    },
    volume_change: {
      description: 'Impact of partner volume changing by ' + toString(COALESCE($partnerVolumeChange, 0)) + '%',
      total_impact: reduce(sum = 0, item IN volume_change_scenario | sum + item.net_change),
      impact_percent: reduce(sum = 0, item IN volume_change_scenario | sum + item.net_change) / total_baseline_net * 100,
      tier_details: volume_change_scenario
    },
    new_partner_acquisition: {
      description: 'Impact of acquiring ' + toString(COALESCE($newPartnerCount, 0)) + ' new partners',
      total_impact: reduce(sum = 0, item IN new_partner_scenario | sum + item.net_change),
      impact_percent: reduce(sum = 0, item IN new_partner_scenario | sum + item.net_change) / total_baseline_net * 100,
      tier_details: new_partner_scenario
    },
    partner_churn: {
      description: 'Impact of ' + toString(COALESCE($churnRate, 0)) + '% partner churn',
      total_impact: reduce(sum = 0, item IN churn_scenario | sum + item.net_change),
      impact_percent: reduce(sum = 0, item IN churn_scenario | sum + item.net_change) / total_baseline_net * 100,
      tier_details: churn_scenario
    }
  },
  break_even_analysis: {
    reward_rate_increase_offset: breakeven_volume_increase_needed,
    new_partner_roi_threshold: revenue_per_new_partner_needed,
    churn_impact_severity: CASE 
      WHEN COALESCE($churnRate, 0) > 20 THEN 'high_risk'
      WHEN COALESCE($churnRate, 0) > 10 THEN 'moderate_risk'
      ELSE 'low_risk'
    END
  },
  risk_assessment: {
    most_sensitive_tier: CASE 
      WHEN size([s IN reward_adjustment_scenario WHERE abs(s.impact_percent) > 20]) > 0
      THEN [s IN reward_adjustment_scenario WHERE abs(s.impact_percent) > 20][0].tier
      ELSE 'none'
    END,
    downside_scenarios: [
      CASE WHEN COALESCE($rewardRateAdjustment, 0) > 0 AND reduce(sum = 0, item IN reward_adjustment_scenario | sum + item.net_change) < 0
           THEN 'reward_rate_increase_hurts_profitability' ELSE NULL END,
      CASE WHEN COALESCE($churnRate, 0) > 15 
           THEN 'high_churn_threatens_revenue_base' ELSE NULL END,
      CASE WHEN COALESCE($partnerVolumeChange, 0) < -10 
           THEN 'volume_decline_reduces_profitability' ELSE NULL END
    ],
    upside_opportunities: [
      CASE WHEN reduce(sum = 0, item IN new_partner_scenario | sum + item.net_change) > total_baseline_net * 0.1
           THEN 'new_partner_acquisition_highly_profitable' ELSE NULL END,
      CASE WHEN COALESCE($partnerVolumeChange, 0) > 20 
           THEN 'volume_growth_significantly_improves_margins' ELSE NULL END
    ]
  },
  recommendations: {
    immediate_actions: CASE 
      WHEN abs(reduce(sum = 0, item IN reward_adjustment_scenario | sum + item.net_change)) > total_baseline_net * 0.1
      THEN ['review_reward_structure_carefully']
      WHEN COALESCE($churnRate, 0) > 15
      THEN ['implement_partner_retention_program']
      ELSE ['monitor_current_performance']
    END,
    strategic_focus: CASE 
      WHEN reduce(sum = 0, item IN new_partner_scenario | sum + item.net_change) > reduce(sum = 0, item IN volume_change_scenario | sum + item.net_change)
      THEN 'prioritize_new_partner_acquisition'
      ELSE 'focus_on_existing_partner_growth'
    END,
    risk_mitigation: [
      CASE WHEN COALESCE($churnRate, 0) > 10 THEN 'develop_churn_prediction_model' ELSE NULL END,
      CASE WHEN abs(COALESCE($rewardRateAdjustment, 0)) > 10 THEN 'pilot_reward_changes_gradually' ELSE NULL END
    ]
  }
} AS revenue_sensitivity_analysis