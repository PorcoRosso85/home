# SpiceDB Authorization POC with Caveats

SpiceDBを使用した認可基盤の概念実証（POC）です。このPOCでは、基本的な権限モデルの実装とCaveats（条件付き権限）への拡張を想定した基盤を提供します。

## 目的

- SpiceDBによる宣言的な認可モデルの実装
- リソース（document等）と主体（user等）の関係定義
- 権限の継承と委譲の実現
- 将来的なCaveats（時間制限、IP制限等の条件付き権限）への拡張基盤

## アーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   SpiceDB   │────▶│   Schema    │
│ Application │     │   Server    │     │ (ZAML形式)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │Relationships│
                    │  (権限関係) │
                    └─────────────┘
```

## セットアップ

### 1. 開発環境の起動

```bash
# Nix開発シェルに入る
nix develop

# 利用可能なコマンドが表示される
# - spicedb: SpiceDBサーバー
# - curl: API通信用
# - jq: JSONデータ処理用
```

### 2. SpiceDBサーバーの起動

```bash
# メモリベースのSpiceDBサーバーを起動
spicedb serve \
  --grpc-preshared-key "your-secret-key" \
  --datastore-engine memory \
  --http-enabled \
  --grpc-addr :50051 \
  --http-addr :8080
```

### 3. スキーマの適用

```bash
# スキーマをSpiceDBに書き込む
./test_schema.sh  # テストスクリプトがスキーマの検証も行います
```

## スキーマ定義

現在の`schema.zaml`では、基本的なドキュメントと権限モデルを定義しています：

```zaml
definition user {}

definition document {
    relation viewer: user
    relation owner: user
    
    permission view = viewer + owner
}
```

- `user`: システムのユーザーを表す
- `document`: 保護されたリソース（ドキュメント）
- `viewer`: ドキュメントの閲覧者
- `owner`: ドキュメントの所有者（閲覧権限も含む）

## 使用例

### 権限関係の作成

```bash
# Aliceをdoc1のviewerとして設定
curl -X POST http://localhost:8080/v1/relationships/write \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-key" \
  -d '{
    "updates": [{
      "operation": "OPERATION_CREATE",
      "relationship": {
        "resource": {"objectType": "document", "objectId": "doc1"},
        "relation": "viewer",
        "subject": {"object": {"objectType": "user", "objectId": "alice"}}
      }
    }]
  }'
```

### 権限チェック

```bash
# Aliceがdoc1を閲覧できるかチェック
curl -X POST http://localhost:8080/v1/permissions/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-key" \
  -d '{
    "resource": {"objectType": "document", "objectId": "doc1"},
    "permission": "view",
    "subject": {"object": {"objectType": "user", "objectId": "alice"}}
  }'
```

## テスト

```bash
# 全体のテストを実行
./test_flake.sh   # Nix環境のテスト
./test_schema.sh  # スキーマと権限チェックのテスト
```

## 今後の拡張予定

### Caveats（条件付き権限）

将来的に以下のような条件付き権限を実装予定：

- 時間制限付きアクセス（期限付き権限）
- IPアドレス制限
- 地理的制限
- カスタム条件（JSONロジック等）

### 例：時間制限付き権限のイメージ

```zaml
definition document {
    relation viewer: user with time_expiry
    relation owner: user
    
    permission view = viewer + owner
}

// 使用例（将来実装）
// document:doc1#viewer@user:alice[expiry:2024-12-31T23:59:59Z]
```

## 参考リンク

- [SpiceDB Documentation](https://authzed.com/docs)
- [SpiceDB Schema Language](https://authzed.com/docs/schema)
- [SpiceDB API Reference](https://authzed.com/docs/api)