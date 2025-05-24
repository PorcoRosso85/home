// LocationURIテーブルの存在とデータの有無を確認するクエリ
// REFACTORED: 最小化されたスキーマに対応（idのみ）
MATCH (n:LocationURI)
RETURN n.id AS id
LIMIT 10
