# KuzuDB UDF POC

KuzuDB User Defined Functions (UDF) の実装例

## 実行方法

```bash
uv run pytest test_kuzu_udf.py -v
```

## テスト内容

1. **extract_scheme UDF** - URI からスキームを抽出
2. **validate_hierarchy UDF** - 階層構造の検証
3. **UDF with aggregation** - 集約関数との組み合わせ
4. **Performance comparison** - UDF vs アプリケーション側処理
5. **count_path_depth UDF** - パス深度の計算

## 例

```python
# UDF登録
def extract_scheme(uri: str) -> str:
    match = re.match(r'^([^:]+)://', uri)
    return match.group(1) if match else ""

conn.create_function("extract_scheme", extract_scheme)

# Cypherクエリ内で使用
MATCH (n:LocationURI)
WHERE extract_scheme(n.id) = 'req'
RETURN count(*)
```