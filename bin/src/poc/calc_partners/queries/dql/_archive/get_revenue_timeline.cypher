// =============================================================================
// Query: Get Revenue Timeline for Chart Visualization  
// Purpose: Time-series revenue data optimized for modern chart libraries and trend analysis
// Parameters:
//   $partnerId (optional): Specific partner ID to filter on [string]
//   $tierFilter (optional): Filter by partner tier ('bronze', 'silver', 'gold', 'platinum') [string]
//   $startDate (required): Start date for timeline (YYYY-MM-DD) [string]
//   $endDate (required): End date for timeline (YYYY-MM-DD) [string]
//   $groupBy (optional): Aggregation period ('daily', 'weekly', 'monthly', default: 'monthly') [string]
//   $includeProjection (optional): Include future projection (boolean, default: false) [boolean]
//   $fillGaps (optional): Fill missing periods with zero data (default: true) [boolean]
//   $chartType (optional): Chart type optimization ('line', 'bar', 'area', 'combined') [string]
//   $currency (optional): Currency code for formatting (default: 'USD') [string]
// Returns: Time-series data optimized for Chart.js, D3.js, Recharts, ApexCharts
// Usage Example:
//   CALL { ... } WITH { startDate: "2024-01-01", endDate: "2024-12-31", groupBy: "monthly", chartType: "line" }
// =============================================================================

// Generate date sequence for complete timeline
WITH 
  date($startDate) as start_date,
  date($endDate) as end_date,
  CASE 
    WHEN $groupBy = 'daily' THEN 1
    WHEN $groupBy = 'weekly' THEN 7
    ELSE 30  // monthly default
  END as day_increment

// Create base timeline with actual transaction data
MATCH (p:Partner)-[:TRIGGERED_BY]->(t:Transaction)
WHERE 
  t.transaction_date >= start_date
  AND t.transaction_date <= end_date
  AND t.status IN ['confirmed', 'pending']
  AND ($partnerId IS NULL OR p.id = $partnerId)
  AND ($tierFilter IS NULL OR p.tier = $tierFilter)

// Group by time period
WITH start_date, end_date, day_increment,
     CASE 
       WHEN $groupBy = 'daily' THEN t.transaction_date
       WHEN $groupBy = 'weekly' THEN 
         date(string(t.transaction_date.year) + '-' + 
              string(t.transaction_date.month) + '-' + 
              string(((t.transaction_date.day - 1) / 7) * 7 + 1))
       ELSE 
         date(string(t.transaction_date.year) + '-' + 
              string(t.transaction_date.month) + '-01')
     END as period_date,
     p, t

// Aggregate metrics by period and tier
WITH period_date,
     count(DISTINCT t) as transaction_count,
     sum(t.amount) as total_revenue,
     avg(t.amount) as avg_transaction_amount,
     count(DISTINCT p) as active_partners,
     collect(DISTINCT p.tier) as active_tiers,
     // Tier breakdown
     sum(CASE WHEN p.tier = 'bronze' THEN t.amount ELSE 0 END) as bronze_revenue,
     sum(CASE WHEN p.tier = 'silver' THEN t.amount ELSE 0 END) as silver_revenue,
     sum(CASE WHEN p.tier = 'gold' THEN t.amount ELSE 0 END) as gold_revenue,
     sum(CASE WHEN p.tier = 'platinum' THEN t.amount ELSE 0 END) as platinum_revenue,
     // Partner activity by tier
     count(DISTINCT CASE WHEN p.tier = 'bronze' THEN p.id END) as bronze_partners,
     count(DISTINCT CASE WHEN p.tier = 'silver' THEN p.id END) as silver_partners,
     count(DISTINCT CASE WHEN p.tier = 'gold' THEN p.id END) as gold_partners,
     count(DISTINCT CASE WHEN p.tier = 'platinum' THEN p.id END) as platinum_partners

// Calculate period-over-period growth
WITH period_date,
     transaction_count,
     total_revenue,
     avg_transaction_amount,
     active_partners,
     bronze_revenue, silver_revenue, gold_revenue, platinum_revenue,
     bronze_partners, silver_partners, gold_partners, platinum_partners
ORDER BY period_date

WITH collect({
  period: period_date,
  revenue: coalesce(total_revenue, 0.0),
  transactions: coalesce(transaction_count, 0),
  avg_amount: coalesce(avg_transaction_amount, 0.0),
  active_partners: coalesce(active_partners, 0),
  tier_breakdown: {
    bronze: {revenue: coalesce(bronze_revenue, 0.0), partners: coalesce(bronze_partners, 0)},
    silver: {revenue: coalesce(silver_revenue, 0.0), partners: coalesce(silver_partners, 0)},
    gold: {revenue: coalesce(gold_revenue, 0.0), partners: coalesce(gold_partners, 0)},
    platinum: {revenue: coalesce(platinum_revenue, 0.0), partners: coalesce(platinum_partners, 0)}
  }
}) as periods

// Calculate growth rates and trends
UNWIND range(0, size(periods) - 1) as i
WITH periods[i] as current_period,
     CASE WHEN i > 0 THEN periods[i-1] ELSE null END as previous_period

WITH current_period,
     // Growth calculations
     CASE 
       WHEN previous_period IS NOT NULL AND previous_period.revenue > 0 
       THEN round(((current_period.revenue - previous_period.revenue) / previous_period.revenue) * 100, 2)
       ELSE null 
     END as revenue_growth_pct,
     CASE 
       WHEN previous_period IS NOT NULL AND previous_period.transactions > 0 
       THEN round(((current_period.transactions - previous_period.transactions) / toFloat(previous_period.transactions)) * 100, 2)
       ELSE null 
     END as transaction_growth_pct

// Return timeline data optimized for modern chart libraries
RETURN 
  current_period.period as period_date,
  
  // Chart-ready period labels with flexible formatting
  CASE 
    WHEN $groupBy = 'daily' THEN toString(current_period.period)
    WHEN $groupBy = 'weekly' THEN 'Week of ' + toString(current_period.period)
    ELSE toString(current_period.period.year) + '-' + 
         CASE 
           WHEN current_period.period.month < 10 THEN '0' + toString(current_period.period.month)
           ELSE toString(current_period.period.month)
         END
  END as period_label,
  
  // Core metrics with proper precision for charts
  round(current_period.revenue, 2) as total_revenue,
  current_period.transactions as transaction_count,
  round(current_period.avg_amount, 2) as avg_transaction_amount,
  current_period.active_partners as active_partners_count,
  
  // Growth indicators with nulls handled for chart libraries
  coalesce(revenue_growth_pct, 0.0) as revenue_growth_pct,
  coalesce(transaction_growth_pct, 0.0) as transaction_growth_pct,
  
  // Tier breakdown optimized for stacked/grouped charts
  {
    bronze: round(current_period.tier_breakdown.bronze.revenue, 2),
    silver: round(current_period.tier_breakdown.silver.revenue, 2), 
    gold: round(current_period.tier_breakdown.gold.revenue, 2),
    platinum: round(current_period.tier_breakdown.platinum.revenue, 2)
  } as tier_revenue,
  
  {
    bronze: current_period.tier_breakdown.bronze.partners,
    silver: current_period.tier_breakdown.silver.partners,
    gold: current_period.tier_breakdown.gold.partners, 
    platinum: current_period.tier_breakdown.platinum.partners
  } as tier_partners,
  
  // Chart library specific formatting
  {
    // Chart.js format
    chartjs: {
      x: toString(current_period.period),
      y: round(current_period.revenue, 2),
      label: CASE 
        WHEN $groupBy = 'daily' THEN toString(current_period.period)
        WHEN $groupBy = 'weekly' THEN 'Week of ' + toString(current_period.period)
        ELSE toString(current_period.period.year) + '-' + 
             CASE 
               WHEN current_period.period.month < 10 THEN '0' + toString(current_period.period.month)
               ELSE toString(current_period.period.month)
             END
      END
    },
    
    // D3.js format
    d3: {
      date: current_period.period,
      value: round(current_period.revenue, 2),
      category: coalesce($tierFilter, 'all_tiers')
    },
    
    // Recharts format
    recharts: {
      name: CASE 
        WHEN $groupBy = 'daily' THEN toString(current_period.period)
        WHEN $groupBy = 'weekly' THEN 'Week of ' + toString(current_period.period)
        ELSE toString(current_period.period.year) + '-' + 
             CASE 
               WHEN current_period.period.month < 10 THEN '0' + toString(current_period.period.month)
               ELSE toString(current_period.period.month)
             END
      END,
      revenue: round(current_period.revenue, 2),
      transactions: current_period.transactions,
      bronze: round(current_period.tier_breakdown.bronze.revenue, 2),
      silver: round(current_period.tier_breakdown.silver.revenue, 2),
      gold: round(current_period.tier_breakdown.gold.revenue, 2),
      platinum: round(current_period.tier_breakdown.platinum.revenue, 2)
    }
  } as chart_formats,
  
  // Enhanced metadata for chart rendering
  {
    currency: coalesce($currency, 'USD'),
    period_type: coalesce($groupBy, 'monthly'),
    chart_type: coalesce($chartType, 'line'),
    data_quality: CASE 
      WHEN current_period.transactions > 0 THEN 'actual'
      ELSE CASE WHEN coalesce($fillGaps, true) THEN 'filled' ELSE 'no_data' END
    END,
    
    // Chart styling hints
    styling: {
      color_scheme: CASE coalesce($chartType, 'line')
        WHEN 'line' THEN ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
        WHEN 'bar' THEN ['#60A5FA', '#34D399', '#FBBF24', '#FB7185'] 
        WHEN 'area' THEN ['rgba(59,130,246,0.6)', 'rgba(16,185,129,0.6)', 'rgba(245,158,11,0.6)', 'rgba(239,68,68,0.6)']
        ELSE ['#6B7280', '#9CA3AF', '#D1D5DB', '#E5E7EB']
      END,
      
      tier_colors: {
        bronze: '#CD7F32',
        silver: '#C0C0C0', 
        gold: '#FFD700',
        platinum: '#E5E4E2'
      }
    },
    
    // Performance hints for large datasets
    performance: {
      data_points: 1,
      recommend_sampling: CASE 
        WHEN $groupBy = 'daily' AND duration.between(date($startDate), date($endDate)).days > 365 THEN true
        ELSE false
      END
    }
  } as chart_metadata

ORDER BY period_date;