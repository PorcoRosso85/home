// 関数型に紐づく戻り値型を取得
MATCH (f:FunctionType)-[:ReturnsType]->(r:ReturnType)
WHERE f.title = $function_title
RETURN r.type, r.description