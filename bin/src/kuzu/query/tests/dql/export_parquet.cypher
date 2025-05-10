// KuzuDBデータエクスポートスクリプト
// データベースをParquet形式でエクスポートします

// データベース全体をエクスポート - すべてのテーブルとデータを含む
EXPORT DATABASE '/home/nixos/bin/src/kuzu/db/export_data' (format="parquet");

// エクスポートの確認
SHOW TABLES;