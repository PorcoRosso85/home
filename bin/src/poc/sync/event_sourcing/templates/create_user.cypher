// Create a new user node
// Parameters: $id, $name, $email, $createdAt
CREATE (u:User {
  id: $id,
  name: $name,
  email: $email,
  createdAt: $createdAt
})
RETURN u