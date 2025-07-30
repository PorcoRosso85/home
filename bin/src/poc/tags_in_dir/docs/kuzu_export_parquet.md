# KuzuDB Export to Parquet

KuzuDBでは`COPY TO`句を使用してクエリ結果をParquetファイルにエクスポートできます。

## 構文例

```cypher
COPY (MATCH (u:User) return u.*) TO 'user.parquet' (compression = 'snappy');
```

## エクスポートオプション

- **圧縮形式**: Snappy（デフォルト）、uncompressed、gzip、lz4、zstd
- サブクエリの結果をエクスポート可能

## 制限事項

- 固定リストデータ型のエクスポートは未サポート
- UNION型はSTRUCT型としてエクスポートされる
- 現在、エクスポートではSnappy圧縮のみサポート

## 検証方法

`LOAD FROM`を使用して生成されたParquetファイルをスキャンできます：

```cypher
LOAD FROM 'user.parquet' RETURN *;
```

## tags_in_dirでの活用

シンボルデータをParquetファイルにエクスポート：

```cypher
COPY (MATCH (s:Symbol) RETURN s.*) TO 'symbols.parquet';
COPY (MATCH (s1:Symbol)-[c:CALLS]->(s2:Symbol) RETURN s1.location_uri, s2.location_uri, c.line_number) TO 'calls.parquet';
```