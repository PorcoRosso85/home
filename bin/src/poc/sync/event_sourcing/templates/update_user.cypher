// Update user properties
// Parameters: $id, $props (object with properties to update)
MATCH (u:User {id: $id})
SET u += $props
SET u.updatedAt = datetime()
RETURN u