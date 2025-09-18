-- Find the parent contract of a child contract
MATCH (p:Contract)-[:PARENT_OF]->(c:Contract {contract_id: $child_id})
OPTIONAL MATCH (p)-[:HAS_TERM]->(t:ContractTerm)
RETURN p, collect(t) as terms