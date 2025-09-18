// Partner ROI Analysis
// Business Value: Identifies profitable vs. unprofitable partner relationships
// Key Insights: 
// - Which partners generate net positive value after reward payments
// - Loss-making agreements that need renegotiation
// - Data-driven partner retention/termination decisions
// - Optimization of reward structures to maintain profitability

MATCH (p:Entity {type: 'partner'})-[i:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
WITH p, COUNT(c) AS customers_introduced, SUM(c.ltv) AS total_customer_value
RETURN 
    p.name AS partner_name,
    customers_introduced,
    total_customer_value,
    total_customer_value * 0.2 AS estimated_rewards,
    total_customer_value - (total_customer_value * 0.2) AS net_profit,
    CASE 
        WHEN total_customer_value - (total_customer_value * 0.2) > 0 THEN 'Profitable'
        ELSE 'Loss-making'
    END AS profitability_status,
    ROUND((total_customer_value - (total_customer_value * 0.2)) / (total_customer_value * 0.2) * 100, 2) AS roi_percentage
ORDER BY net_profit DESC