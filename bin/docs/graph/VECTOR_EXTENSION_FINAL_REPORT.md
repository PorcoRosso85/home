# VECTOR Extension 問題の最終報告書

## 調査日時
2025-08-05

## 重要な発見と証拠

### 1. KuzuDBの拡張機能は動的にダウンロードされる

**参照ドキュメント**:
- KuzuDB公式ドキュメント（Vector Extension）: `/home/nixos/bin/docs/graph/docs/2025-08-05_19-28-28_kuzudb.com_vector.md`
  - Line 17-19: `INSTALL VECTOR;LOAD VECTOR;`の使用方法

**WebFetch結果から**:
> "Extensions are officially hosted and can be installed via the `INSTALL` command. When you run `INSTALL <EXTENSION_NAME>`, Kuzu downloads the extension from its official repository."

### 2. 直接実行テストの成功

**テストコード実行結果**:
```python
# 直接実行すると成功
conn.execute('INSTALL VECTOR')  # ✅ 成功 - QueryResult object returned
conn.execute('LOAD EXTENSION VECTOR')  # ✅ 成功 - QueryResult object returned
```

### 3. vss_kuzuで失敗する真の原因

**問題のあるコード**:
- ファイル: `/home/nixos/bin/src/search/vss_kuzu/vss_kuzu/infrastructure/vector.py`
- 関数: `check_vector_extension` (Line 79-147)
- 問題箇所: Line 96-102

```python
# Just check if CREATE_VECTOR_INDEX function exists
connection.execute(f"""
    CALL CREATE_VECTOR_INDEX(
        'nonexistent_table_{test_table}',
        'test_idx',
        'embedding'
    )
""")
```

**エラーログ**:
```json
{
    "type": "vector_extension_error",
    "message": "VECTOR extension not available",
    "details": {
        "extension": "VECTOR",
        "function": "CREATE_VECTOR_INDEX",
        "raw_error": "Catalog exception: function CREATE_VECTOR_INDEX is not defined. This function exists in the VECTOR extension. You can install and load the extension by running 'INSTALL VECTOR; LOAD EXTENSION VECTOR;'."
    }
}
```

### 4. 自動インストール機能の存在

**参照コード**:
- ファイル: `/home/nixos/bin/src/search/vss_kuzu/vss_kuzu/infrastructure/vector.py`
- 関数: `install_vector_extension` (Line 19-77)
- 呼び出し箇所: Line 124 (`check_vector_extension`内)

vss_kuzuは実際にVECTOR拡張の自動インストール機能を持っていますが、チェック方法に問題があるため、正しく動作していません。

## 結論

### 私の最初の判断の訂正
- ❌ **「ビルド環境の問題」という判断は誤り**
- ❌ **「Nixパッケージ定義の問題」という判断も誤り**
- ✅ **vss_kuzuの`check_vector_extension`実装の問題**

### 推奨対応

1. **短期対応**: 現在のモック使用は妥当な回避策
2. **中期対応**: vss_kuzuの`check_vector_extension`関数を以下のように修正することを推奨

```python
def check_vector_extension(connection: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """VECTOR拡張が利用可能かチェックし、必要ならインストールする"""
    try:
        # まず拡張をインストール・ロード（すでにある場合は無害）
        connection.execute(f"INSTALL {VECTOR_EXTENSION_NAME}")
        connection.execute(f"LOAD EXTENSION {VECTOR_EXTENSION_NAME}")
        return True, None
    except Exception as e:
        # インストール/ロードに失敗した場合のみエラー
        return False, {
            "error": "Failed to install/load VECTOR extension",
            "details": {"raw_error": str(e)}
        }
```

## 参照ファイル一覧

1. **公式ドキュメント**:
   - `/home/nixos/bin/docs/graph/docs/2025-08-05_19-28-28_kuzudb.com_vector.md`

2. **vss_kuzuソースコード**:
   - `/home/nixos/bin/src/search/vss_kuzu/vss_kuzu/infrastructure/vector.py`
   - `/home/nixos/bin/src/search/vss_kuzu/vss_kuzu/application.py`
   - `/home/nixos/bin/src/search/vss_kuzu/vss_kuzu/__init__.py`

3. **テストファイル**:
   - `/home/nixos/bin/docs/graph/flake_graph/test_incremental_indexing_spec.py`

4. **規約ファイル**:
   - `/home/nixos/bin/docs/conventions/prohibited_items.md`
   - `/home/nixos/bin/docs/conventions/testing.md`

## お詫び
拡張機能がビルド時に含める必要があると誤った判断をしてしまいました。
公式ドキュメントとvss_kuzuの実装をより注意深く確認すべきでした。