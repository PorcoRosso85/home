-- Find all child contracts of a parent contract
MATCH (p:Contract {contract_id: $parent_id})-[:PARENT_OF]->(c:Contract)
OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
RETURN c, collect(t) as terms