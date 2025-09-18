-- Upsert contract node (update if exists, create if not)
MERGE (c:Contract {contract_id: $contract_id})
SET c.title = $title,
    c.description = $description,
    c.client_id = $client_id,
    c.client_name = $client_name,
    c.client_email = $client_email,
    c.vendor_id = $vendor_id,
    c.vendor_name = $vendor_name,
    c.vendor_email = $vendor_email,
    c.value_amount = $value_amount,
    c.value_currency = $value_currency,
    c.start_date = $start_date,
    c.end_date = $end_date,
    c.payment_terms = $payment_terms,
    c.status = $status,
    c.created_at = $created_at,
    c.updated_at = $updated_at