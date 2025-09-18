/*
 * Ensure Party Exists (Upsert Pattern)
 * 
 * Creates a party if it doesn't exist, or updates it if it does.
 * This is a composite query that combines check, create, and update operations.
 * Useful for idempotent party creation during contract setup.
 *
 * Parameters:
 * - $id: Unique identifier for the party
 * - $name: Legal name of the party
 * - $type: Type of party (e.g., 'company', 'individual')
 * - $created_at: ISO format timestamp (used only for new parties)
 *
 * Returns:
 * - The party node (either newly created or existing)
 * - operation: 'created' or 'updated' to indicate what happened
 *
 * Example usage:
 * CALL {
 *   id: 'PARTY001',
 *   name: 'Acme Corporation',
 *   type: 'company',
 *   created_at: '2024-01-15T10:00:00Z'
 * }
 *
 * Note: This query uses MERGE with ON CREATE and ON MATCH clauses
 * to handle both creation and update scenarios atomically.
 */

MERGE (p:Party {id: $id})
ON CREATE SET 
    p.name = $name,
    p.type = $type,
    p.created_at = $created_at
ON MATCH SET
    p.name = $name,
    p.type = $type
RETURN p,
       CASE 
           WHEN p.created_at = $created_at THEN 'created'
           ELSE 'updated'
       END as operation