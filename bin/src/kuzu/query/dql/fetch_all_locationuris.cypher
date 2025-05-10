// 全てのLocationURIノードを取得するクエリ
MATCH (locationuri:LocationURI)
RETURN locationuri.uri_id AS uri_id,
       locationuri.scheme AS scheme,
       locationuri.authority AS authority,
       locationuri.path AS path,
       locationuri.fragment AS fragment,
       locationuri.query AS query
