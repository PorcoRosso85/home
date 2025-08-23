// Reward Plan Simulation (What-If Analysis)
// Business Value: Risk-free testing of new reward structures before implementation
// Key Insights:
// - Predict financial impact of different reward rates
// - Model scenarios without affecting production data
// - Compare multiple reward strategies side-by-side
// - Optimize reward rates for maximum partner engagement vs. profitability

// Baseline scenario (15% rate)
MATCH (c:Entity {type: 'customer', source: 'partner'})
RETURN 
    'Current Baseline (15%)' AS scenario_name,
    0.15 AS rate,
    SUM(c.ltv * 0.15) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(c.ltv * 0.15) AS avg_payment_per_customer

UNION ALL

// Aggressive scenario (25% rate)
MATCH (c:Entity {type: 'customer', source: 'partner'})
RETURN 
    'Aggressive Rate (25%)' AS scenario_name,
    0.25 AS rate,
    SUM(c.ltv * 0.25) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(c.ltv * 0.25) AS avg_payment_per_customer

UNION ALL

// Conservative scenario (10% rate)
MATCH (c:Entity {type: 'customer', source: 'partner'})
RETURN 
    'Conservative Rate (10%)' AS scenario_name,
    0.10 AS rate,
    SUM(c.ltv * 0.10) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(c.ltv * 0.10) AS avg_payment_per_customer

UNION ALL

// Tiered scenario (12% for LTV < 5000, 18% for LTV >= 5000)
MATCH (c:Entity {type: 'customer', source: 'partner'})
RETURN 
    'Tiered Structure' AS scenario_name,
    CASE WHEN c.ltv < 5000 THEN 0.12 ELSE 0.18 END AS rate,
    SUM(CASE 
        WHEN c.ltv < 5000 THEN c.ltv * 0.12 
        ELSE c.ltv * 0.18 
    END) AS predicted_total_payment,
    COUNT(c) AS customers_affected,
    AVG(CASE 
        WHEN c.ltv < 5000 THEN c.ltv * 0.12 
        ELSE c.ltv * 0.18 
    END) AS avg_payment_per_customer

ORDER BY predicted_total_payment ASC