// タイトルで関数型を検索
MATCH (f:FunctionType)
WHERE f.title = $title
RETURN f.title, f.description, f.type, f.pure, f.async