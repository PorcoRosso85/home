/*
 * Find Party by ID
 * 
 * Retrieves a party node by its unique identifier.
 * Used to check if a party exists before creating relationships or contracts.
 *
 * Parameters:
 * - $id: Unique identifier of the party to find
 *
 * Returns:
 * - The party node if found
 * - Empty result if not found
 *
 * Example usage:
 * CALL { id: 'PARTY001' }
 */

MATCH (p:Party)
WHERE p.id = $id
RETURN p