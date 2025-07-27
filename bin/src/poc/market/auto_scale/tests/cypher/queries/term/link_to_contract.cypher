-- Create relationship between contract and term
MATCH (c:Contract {contract_id: $contract_id})
MATCH (t:ContractTerm {term_id: $term_id})
MERGE (c)-[:HAS_TERM]->(t)