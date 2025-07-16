# Contract Service POC

異なるスキーマを持つマイクロサービス間の自動通信を実現する仲介サービス。JSON Schemaベースの契約により、データ変換とルーティングを自動化。

## 問題と解決
**問題**: POC独立開発による言語バージョン差異、フィールド名不一致（`location`/`city`）、手動互換性管理  
**解決**: 契約ベース通信、自動マッチング、透過的変換、グラフDB関係管理

## コア機能

### 1. JSON-RPC2 API
```json
// Provider/Consumer統一登録
{"method": "contract.register", "params": {
  "type": "provider",
  "uri": "weather/v1",
  "schema": {"input": {"location": "string"}, "output": {"temperature": "number"}},
  "endpoint": "http://weather:8080"
}}

// 自動変換付き通信
{"method": "contract.call", "params": {
  "from": "dashboard/v2",
  "data": {"city": "Tokyo"}  // 送信側スキーマ
}}
// → {"temp": 25.5, "city": "Tokyo"}  // 自動変換済み
```

### 2. 自動スキーマ変換
- 登録時に互換性判定・`CAN_CALL`関係作成
- 基本マッピング自動生成: `city`↔`location`, `temp`↔`temperature`
- 双方向変換（forward/reverse）対応

### 3. セキュア実行環境
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
(app:App {uri: "weather/v1"}) -[:PROVIDES]-> (schema:Schema)
(app:App {uri: "dashboard/v2"}) -[:EXPECTS]-> (schema:Schema)
// 自動マッチング
(dashboard) -[:CAN_CALL {transform: {...}}]-> (weather)
```

## コア機能（続き）

### 4. バッチリクエスト
```json
// 複数操作を一度に実行
[
  {"jsonrpc": "2.0", "method": "contract.register", "params": {...}, "id": 1},
  {"jsonrpc": "2.0", "method": "contract.register", "params": {...}, "id": 2},
  {"jsonrpc": "2.0", "method": "contract.call", "params": {...}, "id": 3}
]
```

### 5. 変換テスト（ドライラン）
```json
// 実際のProviderを呼ばずに変換を検証
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
│ (Consumer)  │     │   Service    │     │ (Graph Store) │     │  (Provider)  │
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
       │                   │ CREATE Provider Node│                     │
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
       │                   │ CREATE Consumer Node│                     │
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
       │                   │ Find best provider  │                     │
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

