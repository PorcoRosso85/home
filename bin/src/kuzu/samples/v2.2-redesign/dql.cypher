MATCH path = (req:RequirementEntity)-[:DEPENDS_ON*2..]->(req)
RETURN req.title as circular_dependency;