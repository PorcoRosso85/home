# VSS LLM-first Entry Point

## 概要

VSSサービスのLLM-firstなエントリーポイントです。自然言語での対話と構造化されたJSON入力の両方をサポートします。

## 使用方法

### 1. インタラクティブモード（デフォルト）

```bash
nix run /home/nixos/bin/src/search/vss/kuzu
```

READMEが表示され、自然言語で対話できます：
- "認証に関する要件を検索して"
- "ログインに似た要件を5件表示"

### 2. JSON実行モード

単一操作：
```bash
echo '{"operation": "search", "query": "認証システム", "limit": 3}' | \
  nix run /home/nixos/bin/src/search/vss/kuzu#run
```

ファイルから実行：
```bash
nix run /home/nixos/bin/src/search/vss/kuzu#run < examples/index_requirements.json
```

バッチ処理：
```bash
nix run /home/nixos/bin/src/search/vss/kuzu#run < examples/batch_operations.json
```

## 操作一覧

### index - 要件のインデックス作成
```json
{
  "operation": "index",
  "documents": [
    {"id": "REQ001", "content": "ユーザー認証機能を実装する"}
  ]
}
```

### search - 類似検索
```json
{
  "operation": "search",
  "query": "認証システム",
  "limit": 5,
  "threshold": 0.7
}
```

### batch_search - 複数クエリの一括検索
```json
{
  "operation": "batch_search",
  "queries": [
    {"query": "認証", "limit": 3},
    {"query": "ログイン", "limit": 3}
  ]
}
```

## 環境変数

- `VSS_DB_PATH`: データベースパス（デフォルト: `./vss_kuzu_db`）
- `VSS_IN_MEMORY`: インメモリモード（デフォルト: `false`）

## 設計原則

1. **LLM-first**: 自然言語での問い合わせを優先
2. **JSON入力**: 構造化されたバッチ処理をサポート
3. **オプション引数の廃止**: すべての設定はJSONで指定

## テスト

```bash
nix run /home/nixos/bin/src/search/vss/kuzu#test
```