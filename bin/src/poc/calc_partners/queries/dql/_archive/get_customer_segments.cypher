// =============================================================================
// Query: Get Customer Segments Analysis (Partner.tier Focus)
// Purpose: Advanced partner segmentation analysis using Partner.tier for strategic insights and dashboard
// Parameters:
//   $analysisDate (optional): Date for segment analysis (YYYY-MM-DD, default: current date) [string]
//   $segmentBy (optional): Primary segmentation ('tier', 'activity', 'value', 'network', default: 'tier') [string]
//   $includeInactive (optional): Include inactive partners in analysis (boolean, default: false) [boolean]
//   $minTransactionAmount (optional): Minimum transaction filter for active segments [number]
//   $topN (optional): Number of top segments to highlight (default: 5) [integer]
//   $includeProjections (optional): Include growth projections for segments (default: true) [boolean]
//   $benchmarkMode (optional): Enable competitive benchmarking ('internal', 'industry', default: 'internal') [string]
//   $detailLevel (optional): Analysis detail level ('summary', 'detailed', 'executive', default: 'detailed') [string]
// Returns: Comprehensive segment analysis optimized for strategic dashboard and partner management
// Usage Example:
//   CALL { ... } WITH { segmentBy: "tier", detailLevel: "executive", includeProjections: true }
// =============================================================================

// Set enhanced analysis parameters
WITH 
  coalesce(date($analysisDate), date('2024-01-01')) as analysis_date,
  coalesce($segmentBy, 'tier') as segment_by,
  coalesce($includeInactive, false) as include_inactive,
  coalesce($includeProjections, true) as include_projections,
  coalesce($benchmarkMode, 'internal') as benchmark_mode,
  coalesce($detailLevel, 'detailed') as detail_level

// Base partner data with activity metrics
MATCH (p:Partner)
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(t:Transaction)
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(r:Reward)
OPTIONAL MATCH (p)<-[:REFERS]-(referral:Partner)
OPTIONAL MATCH (p)-[:REFERS]->(referred:Partner)

// Filter by activity and date range
WHERE 
  ($includeInactive OR t.transaction_date >= date_sub(analysis_date, duration({months: 6})))
  AND (t.transaction_date IS NULL OR t.transaction_date <= analysis_date)
  AND (t.status IS NULL OR t.status IN ['confirmed', 'pending'])
  AND ($minTransactionAmount IS NULL OR t.amount IS NULL OR t.amount >= $minTransactionAmount)

// Calculate partner-level metrics for segmentation
WITH p,
     count(DISTINCT t) as total_transactions,
     sum(t.amount) as total_revenue,
     avg(t.amount) as avg_transaction_amount,
     count(DISTINCT referral) as referrals_made,
     count(DISTINCT referred) as referrals_received,
     sum(r.amount) as total_rewards,
     max(t.transaction_date) as last_transaction_date,
     min(t.transaction_date) as first_transaction_date,
     // Activity score calculation
     CASE 
       WHEN count(t) > 0 THEN
         (count(DISTINCT t) * 0.3 + 
          coalesce(sum(t.amount), 0) / 1000 * 0.4 + 
          count(DISTINCT referral) * 10 * 0.3)
       ELSE 0
     END as activity_score

// Additional segmentation logic
WITH p, total_transactions, total_revenue, avg_transaction_amount,
     referrals_made, referrals_received, total_rewards,
     last_transaction_date, first_transaction_date, activity_score,
     
     // Value-based segmentation
     CASE 
       WHEN total_revenue >= 10000 THEN 'high_value'
       WHEN total_revenue >= 5000 THEN 'medium_value'
       WHEN total_revenue >= 1000 THEN 'low_value'
       ELSE 'minimal_value'
     END as value_segment,
     
     // Activity-based segmentation  
     CASE 
       WHEN last_transaction_date >= date_sub(analysis_date, duration({months: 1})) THEN 'highly_active'
       WHEN last_transaction_date >= date_sub(analysis_date, duration({months: 3})) THEN 'active'
       WHEN last_transaction_date >= date_sub(analysis_date, duration({months: 6})) THEN 'declining'
       ELSE 'inactive'
     END as activity_segment,
     
     // Network-based segmentation
     CASE 
       WHEN referrals_made >= 10 THEN 'super_networker'
       WHEN referrals_made >= 5 THEN 'active_networker'
       WHEN referrals_made >= 1 THEN 'casual_networker'
       ELSE 'non_networker'
     END as network_segment

// Primary segmentation based on parameter
WITH p, total_transactions, total_revenue, avg_transaction_amount,
     referrals_made, referrals_received, total_rewards,
     last_transaction_date, activity_score,
     value_segment, activity_segment, network_segment,
     
     // Choose primary segment based on parameter
     CASE segment_by
       WHEN 'activity' THEN activity_segment
       WHEN 'value' THEN value_segment  
       WHEN 'network' THEN network_segment
       ELSE coalesce(p.tier, 'unassigned')  // Default to tier
     END as primary_segment

// Aggregate by segment for analysis
WITH primary_segment,
     count(p) as partner_count,
     sum(total_transactions) as segment_transactions,
     sum(total_revenue) as segment_revenue,
     avg(total_revenue) as avg_revenue_per_partner,
     sum(referrals_made) as segment_referrals,
     avg(activity_score) as avg_activity_score,
     sum(total_rewards) as segment_rewards_paid,
     
     // Segment characteristics
     collect({
       partner_id: p.id,
       partner_code: p.code,
       partner_name: p.name,
       tier: p.tier,
       revenue: coalesce(total_revenue, 0),
       transactions: coalesce(total_transactions, 0),
       activity_score: round(activity_score, 2),
       last_active: last_transaction_date
     }) as segment_partners

// Calculate segment performance metrics
WITH primary_segment, partner_count, segment_transactions, segment_revenue,
     avg_revenue_per_partner, segment_referrals, avg_activity_score, 
     segment_rewards_paid, segment_partners,
     
     // Performance indicators
     CASE 
       WHEN avg_revenue_per_partner >= 5000 THEN 'high_performance'
       WHEN avg_revenue_per_partner >= 2000 THEN 'medium_performance'
       WHEN avg_revenue_per_partner >= 500 THEN 'low_performance'
       ELSE 'underperforming'
     END as performance_category,
     
     // ROI calculation (revenue vs rewards)
     CASE 
       WHEN segment_rewards_paid > 0 
       THEN round((segment_revenue - segment_rewards_paid) / segment_rewards_paid * 100, 2)
       ELSE null
     END as segment_roi_pct

// Add segment ranking and percentile analysis
WITH primary_segment, partner_count, segment_transactions, segment_revenue,
     avg_revenue_per_partner, segment_referrals, avg_activity_score,
     segment_rewards_paid, segment_partners, performance_category, segment_roi_pct
ORDER BY segment_revenue DESC

WITH collect({
  segment: primary_segment,
  revenue: segment_revenue,
  count: partner_count,
  avg_revenue: avg_revenue_per_partner
}) as all_segments,
primary_segment, partner_count, segment_transactions, segment_revenue,
avg_revenue_per_partner, segment_referrals, avg_activity_score,
segment_rewards_paid, segment_partners, performance_category, segment_roi_pct

// Calculate percentiles and rankings
WITH primary_segment, partner_count, segment_transactions, segment_revenue,
     avg_revenue_per_partner, segment_referrals, avg_activity_score,
     segment_rewards_paid, segment_partners, performance_category, segment_roi_pct,
     all_segments,
     // Revenue ranking
     reduce(rank = 0, s IN all_segments | 
       CASE WHEN s.revenue > segment_revenue THEN rank + 1 ELSE rank END
     ) + 1 as revenue_rank

// Return enhanced segment analysis optimized for strategic dashboard
RETURN 
  primary_segment as segment_name,
  
  // Segment size and composition with growth metrics
  partner_count,
  round(partner_count / toFloat(reduce(total = 0, s IN all_segments | total + s.count)) * 100, 1) as segment_percentage,
  
  // Financial metrics with precision for dashboard
  round(segment_revenue, 2) as total_revenue,
  round(avg_revenue_per_partner, 2) as avg_revenue_per_partner,
  round(segment_rewards_paid, 2) as total_rewards_paid,
  segment_roi_pct,
  
  // Activity metrics for operational insights
  segment_transactions as total_transactions,
  round(segment_transactions / toFloat(partner_count), 1) as avg_transactions_per_partner,
  segment_referrals as total_referrals,
  round(avg_activity_score, 2) as avg_activity_score,
  
  // Performance indicators and rankings
  performance_category,
  revenue_rank,
  
  // Enhanced tier-specific analysis (when segmenting by tier)
  CASE WHEN segment_by = 'tier' THEN {
    tier_level: CASE primary_segment
      WHEN 'platinum' THEN 4
      WHEN 'gold' THEN 3
      WHEN 'silver' THEN 2
      WHEN 'bronze' THEN 1
      ELSE 0
    END,
    
    tier_thresholds: CASE primary_segment
      WHEN 'bronze' THEN {current: 0, next: 5000, tier_name: 'Silver'}
      WHEN 'silver' THEN {current: 5000, next: 15000, tier_name: 'Gold'}
      WHEN 'gold' THEN {current: 15000, next: 50000, tier_name: 'Platinum'}
      WHEN 'platinum' THEN {current: 50000, next: null, tier_name: 'Elite'}
      ELSE {current: null, next: null, tier_name: 'Unassigned'}
    END,
    
    upgrade_potential: CASE 
      WHEN avg_revenue_per_partner >= 45000 AND primary_segment = 'gold' THEN 'high'
      WHEN avg_revenue_per_partner >= 12000 AND primary_segment = 'silver' THEN 'high'
      WHEN avg_revenue_per_partner >= 4000 AND primary_segment = 'bronze' THEN 'high'
      WHEN avg_revenue_per_partner >= 25000 AND primary_segment = 'gold' THEN 'medium'
      WHEN avg_revenue_per_partner >= 7000 AND primary_segment = 'silver' THEN 'medium'
      WHEN avg_revenue_per_partner >= 2000 AND primary_segment = 'bronze' THEN 'medium'
      ELSE 'low'
    END,
    
    tier_color: CASE primary_segment
      WHEN 'platinum' THEN '#E5E4E2'
      WHEN 'gold' THEN '#FFD700'
      WHEN 'silver' THEN '#C0C0C0'
      WHEN 'bronze' THEN '#CD7F32'
      ELSE '#808080'
    END
  } ELSE null END as tier_insights,
  
  // Growth projections (if enabled)
  CASE WHEN include_projections THEN {
    projected_3m_revenue: round(segment_revenue * 1.05, 2),  // 5% quarterly growth
    projected_6m_revenue: round(segment_revenue * 1.12, 2),  // 12% bi-annual growth
    projected_12m_revenue: round(segment_revenue * 1.25, 2), // 25% annual growth
    
    projected_partner_growth: CASE performance_category
      WHEN 'high_performance' THEN round(partner_count * 1.15, 0)  // 15% growth
      WHEN 'medium_performance' THEN round(partner_count * 1.08, 0) // 8% growth  
      WHEN 'low_performance' THEN round(partner_count * 1.03, 0)    // 3% growth
      ELSE partner_count  // No growth for underperforming
    END,
    
    confidence_level: CASE 
      WHEN performance_category = 'high_performance' THEN 'high'
      WHEN avg_activity_score > 50 THEN 'medium'
      ELSE 'low'
    END
  } ELSE null END as growth_projections,
  
  // Enhanced strategic insights for executive dashboard
  {
    growth_potential: CASE performance_category
      WHEN 'underperforming' THEN 'high'
      WHEN 'low_performance' THEN 'medium' 
      WHEN 'medium_performance' THEN 'medium'
      ELSE 'low'
    END,
    
    investment_priority: CASE 
      WHEN performance_category = 'high_performance' THEN 'retain'
      WHEN performance_category = 'medium_performance' THEN 'develop'
      WHEN performance_category = 'low_performance' THEN 'nurture'
      ELSE 'evaluate'
    END,
    
    risk_level: CASE 
      WHEN avg_activity_score < 10 THEN 'high'
      WHEN avg_activity_score < 50 THEN 'medium'
      ELSE 'low'
    END,
    
    // Strategic recommendations based on segment analysis
    recommendations: CASE 
      WHEN performance_category = 'high_performance' AND primary_segment = 'platinum' 
      THEN ['Implement VIP program', 'Increase engagement touchpoints', 'Provide exclusive benefits']
      WHEN performance_category = 'underperforming' AND avg_activity_score < 10
      THEN ['Implement re-engagement campaign', 'Review reward structure', 'Provide additional support']
      WHEN segment_by = 'tier' AND primary_segment = 'bronze' AND avg_revenue_per_partner > 3000
      THEN ['Consider tier upgrade program', 'Increase reward rates', 'Provide growth incentives']
      ELSE ['Monitor performance', 'Maintain current strategy', 'Regular review']
    END,
    
    // Competitive positioning (if benchmark mode enabled)
    benchmark_position: CASE benchmark_mode
      WHEN 'industry' THEN CASE 
        WHEN avg_revenue_per_partner > 8000 THEN 'above_industry'
        WHEN avg_revenue_per_partner > 3000 THEN 'industry_average'
        ELSE 'below_industry'
      END
      ELSE 'internal_only'
    END
  } as strategic_insights,
  
  // Sample partners for drill-down (adaptive based on detail level)
  CASE detail_level
    WHEN 'executive' THEN [partner IN segment_partners | partner][0..2]  // Top 2 for executives
    WHEN 'summary' THEN [partner IN segment_partners | partner][0..1]    // Top 1 for summary
    ELSE [partner IN segment_partners | partner][0..5]                   // Top 5 for detailed
  END as top_partners,
  
  // Enhanced metadata for dashboard intelligence
  {
    analysis_date: analysis_date,
    segmentation_type: segment_by,
    detail_level: detail_level,
    includes_projections: include_projections,
    benchmark_mode: benchmark_mode,
    total_segments: size(all_segments),
    
    // Dashboard optimization hints
    dashboard_config: {
      chart_type: CASE segment_by
        WHEN 'tier' THEN 'donut'        // Tier distribution works well with donut
        WHEN 'value' THEN 'bar'         // Value segments work well with bar charts
        WHEN 'activity' THEN 'scatter'  // Activity segments work well with scatter
        ELSE 'bar'
      END,
      
      color_scheme: CASE segment_by
        WHEN 'tier' THEN 'metallic'     // Gold, silver, bronze theme
        WHEN 'value' THEN 'green'       // Revenue theme
        WHEN 'activity' THEN 'blue'     // Activity theme
        ELSE 'default'
      END,
      
      refresh_frequency: CASE detail_level
        WHEN 'executive' THEN 'daily'
        WHEN 'detailed' THEN 'hourly'
        ELSE 'real-time'
      END
    },
    
    last_updated: timestamp(),
    data_quality_score: CASE 
      WHEN segment_transactions > 100 THEN 'excellent'
      WHEN segment_transactions > 50 THEN 'good'
      WHEN segment_transactions > 10 THEN 'fair'
      ELSE 'limited'
    END
  } as analysis_metadata

ORDER BY 
  // Dynamic ordering based on detail level and segment type
  CASE 
    WHEN detail_level = 'executive' AND segment_by = 'tier' THEN 
      -CASE primary_segment WHEN 'platinum' THEN 4 WHEN 'gold' THEN 3 WHEN 'silver' THEN 2 WHEN 'bronze' THEN 1 ELSE 0 END
    WHEN $topN IS NOT NULL THEN revenue_rank 
    ELSE 1 
  END,
  segment_revenue DESC
  
LIMIT CASE 
  WHEN detail_level = 'executive' THEN 4    // Limit to 4 segments for executive view
  WHEN detail_level = 'summary' THEN 8      // Limit to 8 segments for summary  
  WHEN $topN IS NOT NULL THEN $topN 
  ELSE 20 
END;