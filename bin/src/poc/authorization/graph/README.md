# KuzuDB Authorization Graph POC

KuzuDBを使用したRBAC/ReBAC認可システムの実装検証

## 概要

このPOCは、リレーショナルデータベースに依存しない、グラフデータベースベースの認可システムの実装可能性を検証します。

### 検証ポイント

1. **運用性**: RDBと比較した権限管理の容易さ
2. **表現力**: 複雑な権限パターンの実装可能性
3. **性能**: 大規模データでの権限チェック速度

## アーキテクチャ

```
○ uri:user/alice
 └─auth→ ○ uri:resource/123
 └─auth→ ○ uri:service/api

すべてのエンティティをURIで統一的に表現
```

## 特徴

- **組み込み可能**: KuzuDBはアプリケーションに直接組み込み可能
- **高速**: グラフトラバーサルによる効率的な権限チェック
- **柔軟**: スキーマレスで動的な権限構造に対応

## 開発環境

```bash
# 開発環境に入る
nix develop

# テスト実行
nix run .#test

# コードフォーマット
nix run .#format

# リント実行
nix run .#lint
```

## ライブラリ使用例

```python
from auth_graph import AuthGraph

# 初期化
auth = AuthGraph("./auth.db")

# 権限付与
auth.grant_permission("user:alice", "resource:123")

# 権限確認
if auth.has_permission("user:alice", "resource:123"):
    print("Access granted")

# 権限削除
auth.revoke_permission("user:alice", "resource:123")
```