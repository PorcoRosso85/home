-- Purpose: Check if a contract exists by ID
-- Description: Verifies whether a contract with the given ID already exists
--              in the database before creating or updating
-- Parameters:
--   $id: STRING - Unique contract identifier (UUID as string)
-- Returns:
--   c: Contract node if exists, null otherwise

MATCH (c:Contract) 
WHERE c.id = $id 
RETURN c