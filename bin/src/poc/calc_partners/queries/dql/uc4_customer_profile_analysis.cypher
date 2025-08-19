// UC4: Customer Profile Analysis by Partner
// Business Value: Understand partner specializations and customer quality patterns
// Key Insights:
// - Which partners consistently bring high-value customers
// - Industry specialization patterns per partner
// - Customer quality metrics (LTV, retention) by source partner
// - Partner-specific customer acquisition strategies optimization

// Main analysis: Customer characteristics by partner
MATCH (p:Entity {type: 'partner', name: $partnerName})-[i:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
RETURN 
    p.name AS partner_name,
    c.industry AS customer_industry,
    COUNT(c) AS customer_count,
    AVG(c.ltv) AS avg_customer_ltv,
    AVG(c.retention_rate) AS avg_retention_rate,
    MIN(c.ltv) AS min_ltv,
    MAX(c.ltv) AS max_ltv,
    SUM(c.ltv) AS total_value_generated,
    ROUND(AVG(c.ltv) / AVG(c.retention_rate) * 100, 2) AS value_efficiency_score

UNION ALL

// Summary: Overall partner performance across all industries  
MATCH (p:Entity {type: 'partner', name: $partnerName})-[i:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
RETURN 
    p.name AS partner_name,
    'ALL_INDUSTRIES' AS customer_industry,
    COUNT(c) AS customer_count,
    AVG(c.ltv) AS avg_customer_ltv,
    AVG(c.retention_rate) AS avg_retention_rate,
    MIN(c.ltv) AS min_ltv,
    MAX(c.ltv) AS max_ltv,
    SUM(c.ltv) AS total_value_generated,
    ROUND(AVG(c.ltv) / AVG(c.retention_rate) * 100, 2) AS value_efficiency_score

UNION ALL

// Comparison: How this partner compares to industry average
MATCH (p:Entity {type: 'partner', name: $partnerName})-[i:INTERACTION {type: 'introduced'}]->(c:Entity {type: 'customer'})
WITH AVG(c.ltv) AS partner_avg_ltv, AVG(c.retention_rate) AS partner_avg_retention
MATCH (all_c:Entity {type: 'customer'})
WITH partner_avg_ltv, partner_avg_retention, AVG(all_c.ltv) AS market_avg_ltv, AVG(all_c.retention_rate) AS market_avg_retention
RETURN 
    $partnerName AS partner_name,
    'MARKET_COMPARISON' AS customer_industry,
    0 AS customer_count,
    partner_avg_ltv AS avg_customer_ltv,
    partner_avg_retention AS avg_retention_rate,
    0.0 AS min_ltv,
    0.0 AS max_ltv,
    0.0 AS total_value_generated,
    ROUND((partner_avg_ltv - market_avg_ltv) / market_avg_ltv * 100, 2) AS value_efficiency_score

ORDER BY avg_customer_ltv DESC