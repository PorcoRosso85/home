-- Purpose: Update an existing contract node in the graph database
-- Description: Updates all properties of an existing contract identified by ID
-- Parameters:
--   $id: STRING - Unique contract identifier (UUID as string)
--   $title: STRING - Updated contract title
--   $description: STRING - Updated contract description
--   $type: STRING - Updated contract type
--   $status: STRING - Updated contract status
--   $value_amount: STRING - Updated contract value amount
--   $value_currency: STRING - Updated currency code
--   $payment_terms: STRING - Updated payment terms
--   $terms: STRING - Updated JSON string containing contract terms
--   $created_at: STRING - Original creation timestamp (preserved)
--   $expires_at: STRING - Updated expiration timestamp
--   $updated_at: STRING - Current update timestamp

MATCH (c:Contract) 
WHERE c.id = $id
SET c.title = $title,
    c.description = $description,
    c.type = $type,
    c.status = $status,
    c.value_amount = $value_amount,
    c.value_currency = $value_currency,
    c.payment_terms = $payment_terms,
    c.terms = $terms,
    c.created_at = $created_at,
    c.expires_at = $expires_at,
    c.updated_at = $updated_at