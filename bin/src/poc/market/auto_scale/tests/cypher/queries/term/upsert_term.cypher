-- Upsert contract term node
MERGE (t:ContractTerm {term_id: $term_id})
SET t.title = $title,
    t.description = $description,
    t.is_mandatory = $is_mandatory