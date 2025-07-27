-- Add parent-child relationship between contracts
MATCH (p:Contract {contract_id: $parent_id})
MATCH (c:Contract {contract_id: $child_id})
MERGE (p)-[:PARENT_OF {relationship_type: $rel_type}]->(c)