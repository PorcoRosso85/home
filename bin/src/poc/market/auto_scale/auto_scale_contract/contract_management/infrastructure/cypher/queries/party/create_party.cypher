/*
 * Create Party Node
 * 
 * Creates a new party (company or individual) in the contract management system.
 * Parties represent entities that can enter into contracts as either buyers or sellers.
 *
 * Parameters:
 * - $id: Unique identifier for the party
 * - $name: Legal name of the party
 * - $type: Type of party (e.g., 'company', 'individual')
 * - $created_at: ISO format timestamp of creation
 *
 * Optional Parameters (for future extension):
 * - $tax_id: Tax identification number
 * - $contact_email: Primary contact email
 * - $contact_phone: Primary contact phone
 * - $address: Business address
 *
 * Example usage:
 * CALL {
 *   id: 'PARTY001',
 *   name: 'Acme Corporation',
 *   type: 'company',
 *   created_at: '2024-01-15T10:00:00Z'
 * }
 */

CREATE (p:Party {
    id: $id,
    name: $name,
    type: $type,
    created_at: $created_at
})
RETURN p