MATCH (req1:RequirementEntity), (req2:RequirementEntity)
WHERE req1.id < req2.id AND req1.resource IS NOT NULL AND req1.resource = req2.resource
RETURN req1.title as service1, req2.title as service2, req1.resource as shared_resource;