// UC3: Reward Plan Simulation (What-If Analysis)
// Business Value: Risk-free testing of new reward structures before implementation
// Key Insights:
// - Predict financial impact of different reward rates
// - Model scenarios without affecting production data
// - Compare multiple reward strategies side-by-side
// - Optimize reward rates for maximum partner engagement vs. profitability

// Simulation Parameters (can be modified for different scenarios)
WITH {
    base_rate: 0.15,        // Current baseline rate
    aggressive_rate: 0.25,  // Higher rate to attract more partners
    conservative_rate: 0.10, // Lower rate to improve margins
    tiered_rate_low: 0.12,  // For customers with LTV < 5000
    tiered_rate_high: 0.18  // For customers with LTV >= 5000
} AS scenarios

MATCH (c:Customer {source: 'partner'})
RETURN 
    'Current Baseline (15%)' AS scenario_name,
    scenarios.base_rate AS rate,
    SUM(c.ltv * scenarios.base_rate) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(c.ltv * scenarios.base_rate) AS avg_payment_per_customer

UNION ALL

MATCH (c:Customer {source: 'partner'})
WITH scenarios, c
RETURN 
    'Aggressive Rate (25%)' AS scenario_name,
    scenarios.aggressive_rate AS rate,
    SUM(c.ltv * scenarios.aggressive_rate) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(c.ltv * scenarios.aggressive_rate) AS avg_payment_per_customer

UNION ALL

MATCH (c:Customer {source: 'partner'})
WITH scenarios, c
RETURN 
    'Conservative Rate (10%)' AS scenario_name,
    scenarios.conservative_rate AS rate,
    SUM(c.ltv * scenarios.conservative_rate) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(c.ltv * scenarios.conservative_rate) AS avg_payment_per_customer

UNION ALL

MATCH (c:Customer {source: 'partner'})
WITH scenarios, c
RETURN 
    'Tiered Structure' AS scenario_name,
    CASE WHEN c.ltv < 5000 THEN scenarios.tiered_rate_low ELSE scenarios.tiered_rate_high END AS rate,
    SUM(CASE 
        WHEN c.ltv < 5000 THEN c.ltv * scenarios.tiered_rate_low 
        ELSE c.ltv * scenarios.tiered_rate_high 
    END) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(CASE 
        WHEN c.ltv < 5000 THEN c.ltv * scenarios.tiered_rate_low 
        ELSE c.ltv * scenarios.tiered_rate_high 
    END) AS avg_payment_per_customer

ORDER BY predicted_total_payment ASC