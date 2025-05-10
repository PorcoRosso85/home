// HAS_LOCATIONエッジを検索するクエリ
MATCH (from:CodeEntity {persistent_id: $from_id})-[has_location:HAS_LOCATION]->(to:LocationURI {uri_id: $to_id})
RETURN from, has_location, to