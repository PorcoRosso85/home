// =============================================================================
// Query: Get Partner Self Dashboard
// Purpose: パートナー自身が確認できるリアルタイム報酬ダッシュボード (Partner Self-Service Dashboard)
// Pain Point: 「パートナーから『今月の報酬、どうなってますか？』っていう問い合わせがウザすぎる。」
// Parameters:
//   $partnerId (required): Partner ID for self-service access [string]
//   $currentMonth (optional): Current month for analysis (YYYY-MM, default: current month) [string]
//   $includeHistory (optional): Include historical performance (default: true) [boolean]
//   $locale (optional): Localization ('en', 'ja', default: 'en') [string]
//   $currency (optional): Currency display (default: 'USD') [string]
//   $timeZone (optional): Timezone for display (default: 'UTC') [string]
//   $showProjections (optional): Show earnings projections (default: true) [boolean]
// Returns: Complete partner self-service dashboard data with real-time status
// Usage Example:
//   CALL { ... } WITH { partnerId: "P001", locale: "ja", showProjections: true }
// =============================================================================

// Parameter setup and validation
WITH 
  $partnerId as partner_id,
  coalesce($currentMonth, toString(date().year) + '-' + 
    CASE WHEN date().month < 10 THEN '0' + toString(date().month) ELSE toString(date().month) END
  ) as current_month,
  coalesce($includeHistory, true) as include_history,
  coalesce($locale, 'en') as locale,
  coalesce($currency, 'USD') as currency,
  coalesce($timeZone, 'UTC') as timezone,
  coalesce($showProjections, true) as show_projections

// Validate partner exists and get basic info
MATCH (p:Partner {id: partner_id})

// Get current month data
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(t_current:Transaction)
WHERE t_current.transaction_date >= date(current_month + '-01')
  AND t_current.transaction_date <= last_day_of_month(date(current_month + '-01'))
  AND t_current.status IN ['confirmed', 'pending', 'completed']

// Get current month rewards
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(r_current:Reward)
WHERE r_current.created_at >= date(current_month + '-01')
  AND r_current.created_at <= last_day_of_month(date(current_month + '-01'))
  AND r_current.status IN ['approved', 'paid']

// Get historical data (last 6 months)
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(t_hist:Transaction)
WHERE t_hist.transaction_date >= date_sub(date(current_month + '-01'), duration({months: 6}))
  AND t_hist.transaction_date < date(current_month + '-01')
  AND t_hist.status IN ['confirmed', 'pending', 'completed']

// Get historical rewards
OPTIONAL MATCH (p)-[:TRIGGERED_BY]->(r_hist:Reward)
WHERE r_hist.created_at >= date_sub(date(current_month + '-01'), duration({months: 6}))
  AND r_hist.created_at < date(current_month + '-01')
  AND r_hist.status IN ['approved', 'paid']

// Get referral network data
OPTIONAL MATCH (p)<-[:REFERS]-(referral:Partner)
OPTIONAL MATCH (p)-[:REFERS]->(referred:Partner)

// Get active reward rules
OPTIONAL MATCH (p)-[ar:APPLIES_RULE]->(rr:RewardRule)
WHERE ar.end_date IS NULL OR ar.end_date >= date()

// Aggregate current month metrics
WITH p, locale, currency, timezone, show_projections, current_month, include_history,
     // Current month aggregations
     count(DISTINCT t_current) as current_transactions,
     sum(t_current.amount) as current_revenue,
     avg(t_current.amount) as current_avg_transaction,
     sum(r_current.amount) as current_rewards,
     count(DISTINCT r_current) as current_reward_events,
     max(t_current.transaction_date) as last_transaction_date,
     
     // Historical aggregations (for comparison)
     count(DISTINCT t_hist) as historical_transactions,
     sum(t_hist.amount) as historical_revenue,
     sum(r_hist.amount) as historical_rewards,
     
     // Network data
     count(DISTINCT referral) as total_referrals_made,
     count(DISTINCT referred) as total_referrals_received,
     
     // Active rules
     collect(DISTINCT {
       rule_id: rr.id,
       type: rr.type,
       rate: rr.rate,
       description: rr.description
     }) as active_rules

// Calculate projections and analytics
WITH p, locale, currency, timezone, show_projections, current_month, include_history,
     current_transactions, current_revenue, current_avg_transaction,
     current_rewards, current_reward_events, last_transaction_date,
     historical_transactions, historical_revenue, historical_rewards,
     total_referrals_made, total_referrals_received, active_rules,
     
     // Calculate monthly averages for projections
     CASE 
       WHEN historical_transactions > 0 THEN historical_revenue / 6.0
       ELSE 0
     END as avg_monthly_revenue,
     
     // Days elapsed in current month
     duration.between(date(current_month + '-01'), date()).days + 1 as days_elapsed,
     
     // Total days in current month
     duration.between(date(current_month + '-01'), last_day_of_month(date(current_month + '-01'))).days + 1 as days_in_month

// Return comprehensive partner self-dashboard
RETURN 
  // Partner Identity
  {
    id: p.id,
    code: p.code,
    name: p.name,
    tier: p.tier,
    member_since: p.created_at,
    
    // Localized tier display
    tier_display: CASE 
      WHEN locale = 'ja' THEN CASE p.tier
        WHEN 'platinum' THEN 'プラチナ'
        WHEN 'gold' THEN 'ゴールド'
        WHEN 'silver' THEN 'シルバー'  
        WHEN 'bronze' THEN 'ブロンズ'
        ELSE '未設定'
      END
      ELSE p.tier
    END,
    
    tier_color: CASE p.tier
      WHEN 'platinum' THEN '#E5E4E2'
      WHEN 'gold' THEN '#FFD700'
      WHEN 'silver' THEN '#C0C0C0'
      WHEN 'bronze' THEN '#CD7F32'
      ELSE '#808080'
    END
  } as partner_info,
  
  // Current Month Performance (Main Dashboard Section)
  {
    month: current_month,
    transactions_count: coalesce(current_transactions, 0),
    total_revenue: round(coalesce(current_revenue, 0.0), 2),
    avg_transaction_amount: round(coalesce(current_avg_transaction, 0.0), 2),
    total_rewards_earned: round(coalesce(current_rewards, 0.0), 2),
    reward_events: coalesce(current_reward_events, 0),
    
    // Performance indicators with localized labels
    performance_label: CASE locale
      WHEN 'ja' THEN CASE 
        WHEN current_transactions >= 10 THEN '非常に活発'
        WHEN current_transactions >= 5 THEN '活発'
        WHEN current_transactions >= 1 THEN '通常'
        ELSE '要活性化'
      END
      ELSE CASE
        WHEN current_transactions >= 10 THEN 'Very Active'
        WHEN current_transactions >= 5 THEN 'Active'
        WHEN current_transactions >= 1 THEN 'Normal'
        ELSE 'Needs Activation'
      END
    END,
    
    // Progress indicators
    progress_to_next_tier: CASE p.tier
      WHEN 'bronze' THEN CASE 
        WHEN current_revenue >= 5000 THEN 100.0
        ELSE round((current_revenue / 5000.0) * 100, 1)
      END
      WHEN 'silver' THEN CASE 
        WHEN current_revenue >= 15000 THEN 100.0
        ELSE round((current_revenue / 15000.0) * 100, 1)
      END
      WHEN 'gold' THEN CASE 
        WHEN current_revenue >= 50000 THEN 100.0
        ELSE round((current_revenue / 50000.0) * 100, 1)
      END
      ELSE null
    END,
    
    last_activity: last_transaction_date
  } as current_month_summary,
  
  // Earnings Projection (if enabled)
  CASE WHEN show_projections THEN {
    projected_month_end_revenue: round(
      CASE 
        WHEN days_elapsed > 0 THEN (current_revenue / days_elapsed) * days_in_month
        ELSE avg_monthly_revenue
      END, 2
    ),
    
    projected_month_end_rewards: round(
      CASE 
        WHEN days_elapsed > 0 THEN (current_rewards / days_elapsed) * days_in_month
        ELSE historical_rewards / 6.0
      END, 2
    ),
    
    confidence_level: CASE 
      WHEN days_elapsed >= 15 THEN 'high'
      WHEN days_elapsed >= 7 THEN 'medium'
      ELSE 'low'
    END,
    
    days_remaining: days_in_month - days_elapsed,
    projection_basis: CASE locale
      WHEN 'ja' THEN CASE 
        WHEN days_elapsed >= 7 THEN '今月の実績ベース'
        ELSE '過去実績ベース'
      END
      ELSE CASE
        WHEN days_elapsed >= 7 THEN 'Based on current month'
        ELSE 'Based on historical data'
      END
    END
  } ELSE null END as projections,
  
  // Historical Performance (if enabled)
  CASE WHEN include_history THEN {
    last_6_months: {
      total_transactions: coalesce(historical_transactions, 0),
      total_revenue: round(coalesce(historical_revenue, 0.0), 2),
      total_rewards: round(coalesce(historical_rewards, 0.0), 2),
      avg_monthly_revenue: round(avg_monthly_revenue, 2),
      
      // Trend comparison
      current_vs_average: CASE 
        WHEN avg_monthly_revenue > 0 
        THEN round(((current_revenue - avg_monthly_revenue) / avg_monthly_revenue) * 100, 1)
        ELSE null
      END
    }
  } ELSE null END as historical_performance,
  
  // Network & Referrals
  {
    referrals_made: total_referrals_made,
    referrals_received: total_referrals_received,
    network_status: CASE 
      WHEN total_referrals_made >= 10 THEN 'super_networker'
      WHEN total_referrals_made >= 5 THEN 'active_networker'
      WHEN total_referrals_made >= 1 THEN 'networker'
      ELSE 'individual'
    END,
    
    network_status_label: CASE locale
      WHEN 'ja' THEN CASE 
        WHEN total_referrals_made >= 10 THEN 'スーパーネットワーカー'
        WHEN total_referrals_made >= 5 THEN 'アクティブネットワーカー'
        WHEN total_referrals_made >= 1 THEN 'ネットワーカー'
        ELSE '個人'
      END
      ELSE CASE
        WHEN total_referrals_made >= 10 THEN 'Super Networker'
        WHEN total_referrals_made >= 5 THEN 'Active Networker'
        WHEN total_referrals_made >= 1 THEN 'Networker'
        ELSE 'Individual'
      END
    END
  } as network_info,
  
  // Active Reward Rules
  {
    total_active_rules: size(active_rules),
    rules: active_rules,
    
    // Rule summary for easy understanding
    rule_summary: CASE locale
      WHEN 'ja' THEN 
        CASE size(active_rules)
          WHEN 0 THEN '適用中の報酬ルールがありません'
          WHEN 1 THEN '1つの報酬ルールが適用中'
          ELSE toString(size(active_rules)) + 'つの報酬ルールが適用中'
        END
      ELSE
        CASE size(active_rules)
          WHEN 0 THEN 'No active reward rules'
          WHEN 1 THEN '1 active reward rule'
          ELSE toString(size(active_rules)) + ' active reward rules'
        END
    END
  } as reward_rules,
  
  // Dashboard Metadata
  {
    currency: currency,
    locale: locale,
    timezone: timezone,
    generated_at: timestamp(),
    
    // Refresh recommendations
    refresh_interval: 300, // 5 minutes for real-time feel
    
    // Localized messages
    messages: CASE locale
      WHEN 'ja' THEN {
        welcome: 'ダッシュボードへようこそ',
        last_updated: '最終更新',
        need_help: '不明な点がありましたら、サポートまでお問い合わせください。',
        tier_progress: '次のティアまでの進捗'
      }
      ELSE {
        welcome: 'Welcome to your dashboard',
        last_updated: 'Last updated',
        need_help: 'Contact support if you have any questions.',
        tier_progress: 'Progress to next tier'
      }
    END,
    
    // Support contact info
    support: {
      enabled: true,
      contact_method: 'dashboard_inquiry',
      auto_context: {
        partner_id: p.id,
        current_tier: p.tier,
        last_activity: last_transaction_date
      }
    }
  } as dashboard_metadata;