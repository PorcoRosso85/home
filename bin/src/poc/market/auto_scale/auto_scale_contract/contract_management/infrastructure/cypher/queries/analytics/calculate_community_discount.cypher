-- Purpose: Calculate dynamic discount rate based on community size
-- Description: Returns the appropriate discount rate for a community based on
--              the number of active members, implementing tiered pricing
-- Parameters:
--   $community_id: STRING - Unique identifier for the community
-- Returns:
--   member_count: INT64 - Number of active members
--   discount_rate: DOUBLE - Calculated discount rate (0.05 to 0.20)

MATCH (c:Contract)-[:ContractParty {role: 'buyer'}]->(p:Party)
WHERE c.type = 'community' 
  AND c.terms CONTAINS $community_id
  AND c.status = 'active'
WITH count(DISTINCT p) as member_count
RETURN 
  member_count,
  CASE 
    WHEN member_count >= 21 THEN 0.20
    WHEN member_count >= 11 THEN 0.15
    WHEN member_count >= 5 THEN 0.10
    ELSE 0.05
  END as discount_rate