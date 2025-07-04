// Delete posts older than a specified date
// Parameters: $beforeDate
MATCH (p:Post)
WHERE p.timestamp < $beforeDate
DETACH DELETE p
RETURN count(p) as deletedCount