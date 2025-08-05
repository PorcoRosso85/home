# VECTOR Extension 問題の真相

## 調査日時
2025-08-05

## 重要な発見

### 1. KuzuDBの拡張機能は動的にダウンロードされる
公式ドキュメントによると：
- `INSTALL VECTOR;` で拡張機能が動的にダウンロードされる
- ビルド時に含める必要はない
- ダウンロードした拡張機能はローカルに保存される

### 2. 実際のテスト結果
```python
# 直接実行すると成功
conn.execute('INSTALL VECTOR')  # ✅ 成功
conn.execute('LOAD EXTENSION VECTOR')  # ✅ 成功
```

### 3. vss_kuzuで失敗する真の原因

**問題のコード**（`vector.py` line 96-102）：
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

このコードは：
1. VECTOR拡張が存在するかチェックするため、CREATE_VECTOR_INDEXを呼び出す
2. 拡張がインストールされていないとエラー
3. エラーを検出して自動インストールを試みる（line 124）
4. しかし、すでにエラーが記録されているため、失敗として扱われる

## 結論

### 私の最初の断言の訂正
- ❌ **「ビルド環境の問題」という判断は誤り**
- ✅ **KuzuDBは拡張機能を動的にダウンロードする**

### vss_kuzuの問題
- `check_vector_extension`関数の実装に問題がある
- VECTOR拡張の存在確認方法が適切でない
- より良い方法：最初にINSTALL/LOADを試みて、失敗したらエラーを返す

## 推奨修正

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

## お詫び
拡張機能がビルド時に含める必要があると誤った判断をしてしまいました。
公式ドキュメントをより注意深く読むべきでした。