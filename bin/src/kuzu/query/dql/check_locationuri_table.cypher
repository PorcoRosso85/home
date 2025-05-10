// LocationURIテーブルの存在とデータの有無を確認するクエリ
MATCH (n)
WHERE has(n.uri_id) // LocationURIノードには uri_id プロパティがある
RETURN n.uri_id AS uri_id,
       n.scheme AS scheme,
       n.path AS path
LIMIT 10
