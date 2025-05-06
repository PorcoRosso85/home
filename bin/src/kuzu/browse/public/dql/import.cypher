-- KuzuDB Parquetインポートスクリプト
-- エクスポートされたParquetファイルをkuzu-wasmにインポートします

-- エクスポートされたスキーマファイルを使用してテーブルを作成
SOURCE '/export_data/schema.cypher';

-- エクスポートされたcopy.cypherを使用してデータをインポート
SOURCE '/export_data/copy.cypher';

-- インポート結果の確認
MATCH (n) RETURN count(n) as NodeCount;
MATCH ()-[r]->() RETURN count(r) as RelationshipCount;
