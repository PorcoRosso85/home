-- Find contract by ID with related terms
MATCH (c:Contract {contract_id: $contract_id})
OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
RETURN c, collect(t) as terms