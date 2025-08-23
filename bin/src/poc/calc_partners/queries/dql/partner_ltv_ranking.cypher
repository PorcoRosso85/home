// Partner LTV Ranking
// Business Value: Identify most profitable partners at a glance
// 
// This query answers the critical question: "Which partners are bringing the most valuable customers?"
// Instead of just counting customer quantity, this focuses on quality - total lifetime value generated.
//
// Use Case: An executive needs to quickly identify which partner relationships deserve the most attention
// and investment. This ranking reveals the golden partners who consistently introduce high-value customers.

MATCH (p:Entity {type: 'partner'})-[:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
WITH p, COUNT(DISTINCT c) AS customer_count, SUM(c.ltv) AS total_ltv
RETURN 
    p.name AS partner_name,
    customer_count,
    total_ltv
ORDER BY total_ltv DESC;

// Expected Output Example:
// ┌──────────────┬────────────────┬───────────┐
// │ partner_name │ customer_count │ total_ltv │
// ├──────────────┼────────────────┼───────────┤
// │ "Gold Corp"  │ 12            │ 2,400,000 │
// │ "Silver Inc" │ 8             │ 1,800,000 │
// │ "Bronze Ltd" │ 15            │ 1,200,000 │
// └──────────────┴────────────────┴───────────┘
//
// Key Insights:
// - Gold Corp: Fewer customers (12) but highest total LTV - premium customer quality
// - Bronze Ltd: Most customers (15) but lowest total LTV - volume play with lower-value customers
// - This ranking helps prioritize partner relationship investments based on actual financial impact