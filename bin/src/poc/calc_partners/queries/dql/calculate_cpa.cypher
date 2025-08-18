// =============================================================================
// Query: Calculate CPA (Customer Acquisition Cost)
// Purpose: Calculate the cost of acquiring new customers/partners through referrals
// Pain Point: Track acquisition efficiency and optimize referral program costs
// =============================================================================
//
// Parameters:
// - $startDate: Start date for acquisition period (DATE, e.g., '2024-01-01')
// - $endDate: End date for acquisition period (DATE, e.g., '2024-12-31')
// - $referrerPartnerId: Optional - Calculate CPA for specific referrer (INT64, null for all)
// - $targetTier: Optional - Calculate CPA for specific partner tier (STRING, null for all)
// - $acquisitionCost: Total acquisition costs for the period (DECIMAL, e.g., 10000.00)
//
// Returns:
// - referrer_id: ID of the referring partner (null for overall)
// - referrer_name: Name of the referring partner
// - acquired_count: Number of partners acquired
// - total_acquisition_value: Total value of acquired partners
// - cpa: Cost Per Acquisition (total cost / acquired count)
// - avg_partner_value: Average value per acquired partner
// - roi_ratio: Return on Investment ratio (value / cost)
//
// =============================================================================

MATCH (referrer:Partner)-[r:REFERS]->(acquired:Partner)
WHERE r.referred_date >= $startDate 
  AND r.referred_date <= $endDate
  AND r.status = 'active'
  AND ($referrerPartnerId IS NULL OR referrer.id = $referrerPartnerId)
  AND ($targetTier IS NULL OR acquired.tier = $targetTier)

WITH referrer, 
     COUNT(acquired) AS acquired_count,
     SUM(acquired.value) AS total_acquisition_value,
     $acquisitionCost AS total_cost

RETURN 
  referrer.id AS referrer_id,
  referrer.name AS referrer_name,
  acquired_count,
  total_acquisition_value,
  CASE 
    WHEN acquired_count > 0 THEN ROUND(total_cost / acquired_count, 2)
    ELSE 0.0
  END AS cpa,
  CASE 
    WHEN acquired_count > 0 THEN ROUND(total_acquisition_value / acquired_count, 2)
    ELSE 0.0
  END AS avg_partner_value,
  CASE 
    WHEN total_cost > 0 THEN ROUND(total_acquisition_value / total_cost, 4)
    ELSE 0.0
  END AS roi_ratio

ORDER BY acquired_count DESC, total_acquisition_value DESC;

// =============================================================================
// Example Usage:
// 
// 1. Calculate overall CPA for Q1 2024 with $50,000 acquisition budget:
// {
//   "startDate": "2024-01-01",
//   "endDate": "2024-03-31", 
//   "referrerPartnerId": null,
//   "targetTier": null,
//   "acquisitionCost": 50000.00
// }
//
// 2. Calculate CPA for specific referrer partner (ID: 123):
// {
//   "startDate": "2024-01-01",
//   "endDate": "2024-12-31",
//   "referrerPartnerId": 123,
//   "targetTier": null,
//   "acquisitionCost": 25000.00
// }
//
// 3. Calculate CPA for acquiring "premium" tier partners:
// {
//   "startDate": "2024-01-01",
//   "endDate": "2024-12-31",
//   "referrerPartnerId": null,
//   "targetTier": "premium",
//   "acquisitionCost": 75000.00
// }
// =============================================================================