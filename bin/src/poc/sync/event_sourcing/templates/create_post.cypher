// Create a post authored by a user
// Parameters: $postId, $userId, $content, $timestamp
MATCH (u:User {id: $userId})
CREATE (p:Post {
  id: $postId,
  content: $content,
  timestamp: $timestamp
})
CREATE (u)-[a:AUTHORED {
  at: $timestamp
}]->(p)
RETURN u, a, p