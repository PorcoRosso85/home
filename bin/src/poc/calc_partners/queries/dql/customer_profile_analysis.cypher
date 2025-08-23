// UC4: Customer Profile Analysis by Partner
// Business Value: Understand partner specializations and customer quality patterns
// Key Insights:
// - Which partners consistently bring high-value customers
// - Industry specialization patterns per partner
// - Customer quality metrics (LTV, retention) by source partner
// - Partner-specific customer acquisition strategies optimization

// Analysis: Customer characteristics by specific partner
MATCH (p:Entity {type: 'partner', name: $partnerName})-[i:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
WITH p, COUNT(c) AS total_customers, AVG(c.ltv) AS avg_ltv, MIN(c.ltv) AS min_ltv, MAX(c.ltv) AS max_ltv
RETURN 
    p.name AS partner_name,
    total_customers,
    avg_ltv,
    min_ltv,
    max_ltv
ORDER BY avg_ltv DESC