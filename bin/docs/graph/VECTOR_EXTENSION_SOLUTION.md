# VECTOR Extension Solution

## 問題
KuzuDBのVECTOR extensionが現在の環境で利用できない

## 原因
KuzuDBのVECTOR extensionは別途インストールが必要:
```sql
INSTALL VECTOR;
LOAD EXTENSION VECTOR;
```

## 解決案

### 1. 短期対応（現状維持）
- テストではモックを使用してVECTOR extension依存を回避
- 本番環境でのみVECTOR extensionを使用

### 2. 中期対応（推奨）
vss_kuzu flakeでVECTOR extensionの自動インストールを実装:

```python
# vss_kuzu/application/create_vss.py の改善案
def create_vss(db_path: str, ...):
    # DB接続後、自動的にVECTOR extensionをインストール
    connection.execute("INSTALL VECTOR IF NOT EXISTS;")
    connection.execute("LOAD EXTENSION VECTOR;")
```

### 3. 長期対応
Nix flakeでKuzuDBビルド時にVECTOR extensionを含める:
- kuzu_py flakeでVECTOR extension含めたビルド
- または、別途vector-extension flakeを作成

## 参考資料
- KuzuDB Vector Extension公式ドキュメント: ./docs/2025-08-05_19-28-28_kuzudb.com_vector.md