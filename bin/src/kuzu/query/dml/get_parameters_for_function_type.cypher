// 関数型に紐づくパラメータを取得
MATCH (f:FunctionType)-[r:HasParameter]->(p:Parameter)
WHERE f.title = $function_title
RETURN p.name, p.type, p.description, p.required, r.order_index
ORDER BY r.order_index