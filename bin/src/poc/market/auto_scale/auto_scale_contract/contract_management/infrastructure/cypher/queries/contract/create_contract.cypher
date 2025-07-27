-- Purpose: Create a new contract node in the graph database
-- Description: Creates a contract node with all required properties including
--              financial details, validity period, and associated terms
-- Parameters:
--   $id: STRING - Unique contract identifier (UUID as string)
--   $title: STRING - Contract title
--   $description: STRING - Contract description (can be empty)
--   $type: STRING - Contract type (e.g., 'reseller', 'service')
--   $status: STRING - Contract status (e.g., 'DRAFT', 'ACTIVE', 'TERMINATED')
--   $value_amount: STRING - Contract value amount as string
--   $value_currency: STRING - Currency code (e.g., 'USD', 'EUR')
--   $payment_terms: STRING - Payment terms (e.g., 'NET_30', 'NET_60')
--   $terms: STRING - JSON string containing contract terms array
--   $created_at: STRING - ISO format creation timestamp
--   $expires_at: STRING - ISO format expiration timestamp
--   $updated_at: STRING - ISO format last update timestamp

CREATE (c:Contract {
    id: $id,
    title: $title,
    description: $description,
    type: $type,
    status: $status,
    value_amount: $value_amount,
    value_currency: $value_currency,
    payment_terms: $payment_terms,
    terms: $terms,
    created_at: $created_at,
    expires_at: $expires_at,
    updated_at: $updated_at
})