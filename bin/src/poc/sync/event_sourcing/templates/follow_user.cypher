// Create a FOLLOWS relationship between users
// Parameters: $followerId, $targetId, $timestamp
MATCH (follower:User {id: $followerId})
MATCH (target:User {id: $targetId})
WHERE NOT (follower)-[:FOLLOWS]->(target)
CREATE (follower)-[f:FOLLOWS {
  since: $timestamp
}]->(target)
RETURN follower, f, target