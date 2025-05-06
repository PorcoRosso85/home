-- KuzuDB Parquetインポートスクリプト
-- エクスポートされたParquetファイルをkuzu-wasmにインポートします

-- エクスポートされたスキーマファイルを使用してテーブルを作成
SOURCE '/export_data/schema.cypher';

-- エクスポートされたcopy.cypherを使用してデータをインポート
SOURCE '/export_data/copy.cypher';

-- インポート結果の確認
MATCH (n) RETURN count(n) as NodeCount;
MATCH ()-[r]->() RETURN count(r) as RelationshipCount;

-- テーブル一覧とレコード数を表示
SHOW TABLES;

-- 各ノードの数を表示
MATCH (n) 
WITH labels(n) AS nodeType
RETURN nodeType[0] AS TableName, count(*) AS RecordCount
ORDER BY RecordCount DESC;

-- 各リレーションシップの数を表示
MATCH ()-[r]->() 
WITH type(r) AS relType
RETURN relType AS RelationshipName, count(*) AS RecordCount
ORDER BY RecordCount DESC;