// {table_name}エッジを作成するクエリ
MATCH (from:{from_table} {{{from_match}}})
MATCH (to:{to_table} {{{to_match}}})
CREATE (from)-[{var}:{table_name} {{{properties}}}]->(to)
RETURN {var}
