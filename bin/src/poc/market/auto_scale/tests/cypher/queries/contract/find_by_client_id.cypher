-- Find contracts by client ID
MATCH (c:Contract {client_id: $client_id})
OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
RETURN c, collect(t) as terms