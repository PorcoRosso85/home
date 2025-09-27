# Contract Service POC

あるサービスは`city`、別のサービスは`location`。同じ意味なのに通信できない... Contract Serviceがこの違いを自動で吸収し、マイクロサービス間の「翻訳者」として機能します。JSON Schemaベースの契約により、データ変換とルーティングを自動化。

## 問題と解決
**問題**: POC独立開発による言語バージョン差異、フィールド名不一致（`location`/`city`）、手動互換性管理  
**解決**: 契約ベース通信、自動マッチング、透過的変換、グラフDB関係管理

## コア機能

### 1. JSON-RPC2 API
```json
// App(provider)登録（スキーマファイルパス必須）
{"method": "contract.register", "params": {
  "type": "provider",
  "uri": "weather/v1",
  "inputSchemaPath": "/path/to/input.schema.json",
  "outputSchemaPath": "/path/to/output.schema.json",
  "endpoint": "http://weather:8080"
}}

// App(consumer)登録
{"method": "contract.register", "params": {
  "type": "consumer",
  "uri": "dashboard/v2",
  "expectsInputSchemaPath": "/path/to/expects-input.schema.json",
  "expectsOutputSchemaPath": "/path/to/expects-output.schema.json"
}}

// 自動変換付き通信
{"method": "contract.call", "params": {
  "from": "dashboard/v2",
  "data": {"city": "Tokyo"}  // 送信側スキーマ
}}
// → {"temp": 25.5, "city": "Tokyo"}  // 自動変換済み
```

### 2. スキーマファイル要件
- **必須**: 全てのサービスはJSON Schemaファイルパスで契約を定義
- **検証**: ファイル存在確認、JSON妥当性、JSON Schema形式検証
- **相対パス対応**: `./schema.json`は実行ディレクトリ基準で解決

### 3. 自動スキーマ変換
- 登録時に互換性判定・`CAN_CALL`関係作成
- 基本マッピング自動生成: `city`↔`location`, `temp`↔`temperature`
- 双方向変換（forward/reverse）対応

### 4. セキュア実行環境
- 変換スクリプトはWorker分離（権限なし）
- カスタム変換も安全に実行:
```javascript
function transform(input) {
  return {location: input.city.toUpperCase()};
}
```

## 技術選定
- **Deno/TypeScript**: Worker isolation標準対応
- **JSON-RPC2**: バッチ処理、構造化エラー
- **KuzuDB**: グラフ構造でサービス関係を自然に表現

## グラフDB構造
```cypher
// サービス登録時
(provider:App(provider) {uri: "weather/v1"}) -[:PROVIDES]-> (schema:Schema)
(consumer:App(consumer) {uri: "dashboard/v2"}) -[:EXPECTS]-> (schema:Schema)
// 自動マッチング
(consumer) -[:CAN_CALL {transform: {...}}]-> (provider)
```

## コア機能（続き）

### 5. バッチリクエスト
```json
// 複数操作を一度に実行
[
  {"jsonrpc": "2.0", "method": "contract.register", "params": {...}, "id": 1},
  {"jsonrpc": "2.0", "method": "contract.register", "params": {...}, "id": 2},
  {"jsonrpc": "2.0", "method": "contract.call", "params": {...}, "id": 3}
]
```

### 6. 変換テスト（ドライラン）
```json
// 実際のApp(provider)を呼ばずに変換を検証
{"method": "contract.test", "params": {
  "from": "dashboard/v2",
  "to": "weather/v1",
  "testData": {"city": "Tokyo"},
  "dryRun": true
}}
// → 変換ステップを可視化して返却
{
  "steps": [
    {"step": "input", "data": {"city": "Tokyo"}},
    {"step": "transformed", "data": {"location": "Tokyo"}},
    {"step": "mockResponse", "data": {"temp": 20, "humidity": 50}},
    {"step": "output", "data": {"temp": 20, "humid": 50, "city": "Tokyo"}}
  ]
}
```

## ユーザーフロー例（シーケンス図）

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Dashboard  │     │   Contract   │     │     KuzuDB    │     │   Weather    │
│(App:consumer)│     │   Service    │     │ (Graph Store) │     │(App:provider)│
└──────┬──────┘     └──────┬───────┘     └───────┬───────┘     └──────┬───────┘
       │                   │                     │                     │
       │                   │                     │                     │
   ┌───┴───────────────────┴─────────────────────┴─────────────────────┴───┐
   │                      1. サービス登録フェーズ                            │
   └───────────────────────────────────────────────────────────────────────┘
       │                   │                     │                     │
       │                   │<────────────────────┼─────────────────────┤
       │                   │ POST /rpc           │                     │
       │                   │ contract.register   │                     │
       │                   │ {type:"provider",   │                     │
       │                   │  uri:"weather/v1",  │                     │
       │                   │  schema:{...}}      │                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │CREATE App(provider) │                     │
       │                   │ + Schema            │                     │
       │                   │<────────────────────┤                     │
       │                   │                     │                     │
       │                   ├─────────────────────┼─────────────────────>
       │                   │ Response: {status:"registered",           │
       │                   │           provider:"weather/v1"}          │
       │                   │                     │                     │
       ├──────────────────>│                     │                     │
       │ POST /rpc         │                     │                     │
       │ contract.register │                     │                     │
       │ {type:"consumer", │                     │                     │
       │  uri:"dash/v2",   │                     │                     │
       │  expects:{...}}   │                     │                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │CREATE App(consumer) │                     │
       │                   │ + Auto-match        │                     │
       │                   │<────────────────────┤                     │
       │                   │                     │                     │
       │<──────────────────┤                     │                     │
       │ Response:         │                     │                     │
       │ {status:"registered",                   │                     │
       │  consumer:"dash/v2",                     │                     │
       │  providers:[...]} │                     │                     │
       │                   │                     │                     │
       │                   │                     │                     │
   ┌───┴───────────────────┴─────────────────────┴─────────────────────┴───┐
   │                       2. 実行時の通信フロー                            │
   └───────────────────────────────────────────────────────────────────────┘
       │                   │                     │                     │
   [User Action]           │                     │                     │
       │                   │                     │                     │
       ├──────────────────>│                     │                     │
       │ POST /rpc         │                     │                     │
       │ contract.call     │                     │                     │
       │ {from:"dash/v2",  │                     │                     │
       │  data:{           │                     │                     │
       │   city:"Tokyo"}}  │                     │                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │Find best App(provider)│                     │
       │                   │ + transform rules   │                     │
       │                   │<────────────────────┤                     │
       │                   │ weather/v1 endpoint │
       │                   │                     │                     │
       │               ┌───┴───┐                 │                     │
       │               │Transform                │                     │
       │               │Forward │                │                     │
       │               └───┬───┘                 │                     │
       │                   │                     │                     │
       │                   ├─────────────────────┼─────────────────────>
       │                   │ POST to endpoint    │                     │
       │                   │ {location:"Tokyo"}  │                     │
       │                   │<────────────────────┼─────────────────────┤
       │                   │ Response data       │                     │
       │                   │                     │                     │
       │               ┌───┴───┐                 │                     │
       │               │Transform                │                     │
       │               │Reverse │                │                     │
       │               └───┬───┘                 │                     │
       │                   │                     │                     │
       │<──────────────────┤                     │                     │
       │ Transformed data  │                     │                     │
       │                   │                     │                     │
```

### エラーハンドリング
```json
// スキーマ不一致
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32002,
    "message": "Schema transformation failed",
    "data": {
      "missing": ["altitude"],
      "incompatible": [{"field": "date", "expected": "ISO8601"}]
    }
  },
  "id": 1
}
```

## 開発・テスト

```bash
# 開発環境起動
nix develop
deno task dev  # http://localhost:8000/rpc

# テスト実行（JSON-RPC2 E2E）
deno task test
```

