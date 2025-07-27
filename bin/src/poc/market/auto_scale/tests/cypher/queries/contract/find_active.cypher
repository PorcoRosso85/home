-- Find all active contracts
MATCH (c:Contract {status: $status})
OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
RETURN c, collect(t) as terms