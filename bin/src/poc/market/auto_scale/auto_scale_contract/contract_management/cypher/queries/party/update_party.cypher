/*
 * Update Party Node
 * 
 * Updates an existing party's information in the contract management system.
 * This query only updates the provided fields, preserving other properties.
 *
 * Parameters:
 * - $id: Unique identifier of the party to update
 * - $name: Updated legal name of the party
 * - $type: Updated type of party
 *
 * Optional Parameters (for future extension):
 * - $tax_id: Updated tax identification number
 * - $contact_email: Updated primary contact email
 * - $contact_phone: Updated primary contact phone
 * - $address: Updated business address
 * - $updated_at: Timestamp of the update
 *
 * Returns:
 * - The updated party node
 *
 * Example usage:
 * CALL {
 *   id: 'PARTY001',
 *   name: 'Acme Corporation Ltd.',
 *   type: 'company'
 * }
 */

MATCH (p:Party)
WHERE p.id = $id
SET p.name = $name,
    p.type = $type
RETURN p