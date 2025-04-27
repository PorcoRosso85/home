// 関数型と戻り値型の関連付け
MATCH (f:FunctionType), (r:ReturnType)
WHERE f.title = $function_title AND r.type = $return_type
CREATE (f)-[:ReturnsType]->(r)