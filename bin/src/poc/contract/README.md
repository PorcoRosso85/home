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

## ユーザーフロー例（シーケンス図）

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Dashboard  │     │   Contract   │     │     KuzuDB    │     │   Weather    │
│    (App)    │     │   Service    │     │ (Graph Store) │     │    (App)     │
└──────┬──────┘     └──────┬───────┘     └───────┬───────┘     └──────┬───────┘
       │                   │                     │                     │
       │                   │                     │                     │
   ┌───┴───────────────────┴─────────────────────┴─────────────────────┴───┐
   │                      1. アプリケーション登録フェーズ                      │
   └───────────────────────────────────────────────────────────────────────┘
       │                   │                     │                     │
       │                   │<────────────────────┼─────────────────────┤
       │                   │ POST /rpc           │                     │
       │                   │ app.register        │                     │
       │                   │ {uri:"weather/v1",  │                     │
       │                   │  endpoint:"http..", │                     │
       │                   │  metadata:{...}}    │                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │ CREATE (a:App {     │                     │
       │                   │   uri:"weather/v1", │                     │
       │                   │   endpoint:".."})   │                     │
       │                   │<────────────────────┤                     │
       │                   │                     │                     │
       │                   ├─────────────────────┼─────────────────────>
       │                   │ Response: {status:"registered",           │
       │                   │           app:"weather/v1"}                │
       │                   │                     │                     │
       ├──────────────────>│                     │                     │
       │ POST /rpc         │                     │                     │
       │ app.register      │                     │                     │
       │ {uri:"dash/v2",   │                     │                     │
       │  endpoint:null,   │                     │                     │
       │  metadata:{...}}  │                     │                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │ CREATE (a:App {     │                     │
       │                   │   uri:"dash/v2"})   │                     │
       │                   │<────────────────────┤                     │
       │                   │                     │                     │
       │<──────────────────┤                     │                     │
       │ Response:         │                     │                     │
       │ {status:"registered",                   │                     │
       │  app:"dash/v2"}   │                     │                     │
       │                   │                     │                     │
       │                   │                     │                     │
   ┌───┴───────────────────┴─────────────────────┴─────────────────────┴───┐
   │                    2. ルーティング設定フェーズ                          │
   └───────────────────────────────────────────────────────────────────────┘
       │                   │                     │                     │
       │                   │<────────────────────┼─────────────────────┤
       │                   │ POST /rpc           │                     │
       │                   │ route.provide       │                     │
       │                   │ {app:"weather/v1",  │                     │
       │                   │  schema:{           │                     │
       │                   │   input:{location}, │                     │
       │                   │   output:{temp,..}}}│                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │ CREATE (s:Schema)   │                     │
       │                   │ CREATE (a)-[:PROVIDES]->(s)               │
       │                   │<────────────────────┤                     │
       │                   │                     │                     │
       │                   ├─────────────────────┼─────────────────────>
       │                   │ Response: {status:"route_created"}        │
       │                   │                     │                     │
       ├──────────────────>│                     │                     │
       │ POST /rpc         │                     │                     │
       │ route.consume     │                     │                     │
       │ {app:"dash/v2",   │                     │                     │
       │  expects:{        │                     │                     │
       │   output:{city},  │                     │                     │
       │   input:{temp,..}}│                     │                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │ CREATE (s:Schema)   │                     │
       │                   │ CREATE (a)-[:EXPECTS]->(s)                │
       │                   │ Auto-match:         │                     │
       │                   │ CREATE (dash)-[:CAN_CALL {               │
       │                   │   transform:{...}   │                     │
       │                   │ }]->(weather)       │                     │
       │                   │<────────────────────┤                     │
       │                   │                     │                     │
       │<──────────────────┤                     │                     │
       │ Response:         │                     │                     │
       │ {routes:[         │                     │                     │
       │   {to:"weather",  │                     │                     │
       │    transform:{    │                     │                     │
       │     forward:{city->location},          │                     │
       │     reverse:{temp<-temperature}        │                     │
       │   }}]}            │                     │                     │
       │                   │                     │                     │
       │                   │                     │                     │
   ┌───┴───────────────────┴─────────────────────┴─────────────────────┴───┐
   │                       3. 実行時の通信フロー                            │
   └───────────────────────────────────────────────────────────────────────┘
       │                   │                     │                     │
   [User Action]           │                     │                     │
       │                   │                     │                     │
       ├──────────────────>│                     │                     │
       │ POST /rpc         │                     │                     │
       │ route.call        │                     │                     │
       │ {from:"dash/v2",  │                     │                     │
       │  data:{           │                     │                     │
       │   city:"Tokyo"}}  │                     │                     │
       │                   │                     │                     │
       │                   ├────────────────────>│                     │
       │                   │ MATCH (from:App)-[:CAN_CALL]->(to:App)   │
       │                   │ WHERE from.uri=$from│                     │
       │                   │<────────────────────┤                     │
       │                   │ weather/v1 + transform + endpoint         │
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

### API設計（JSON-RPC2）

現在の実装では`contract.register`、`contract.call`などのメソッドを使用していますが、
将来的には以下のようなアプリケーション中心の設計に移行予定です：

#### アプリケーション登録
```json
// Request
{
  "jsonrpc": "2.0",
  "method": "app.register",
  "params": {
    "uri": "services/weather/v1",
    "endpoint": "http://weather:8080/rpc",
    "metadata": {
      "version": "1.0.0",
      "description": "Weather information service"
    }
  },
  "id": 1
}
```

#### ルーティング設定
```json
// Provider側の設定
{
  "jsonrpc": "2.0",
  "method": "route.provide",
  "params": {
    "app": "services/weather/v1",
    "schema": {
      "input": {"location": "string"},
      "output": {"temperature": "number", "humidity": "number"}
    }
  },
  "id": 2
}

// Consumer側の設定
{
  "jsonrpc": "2.0",
  "method": "route.consume",
  "params": {
    "app": "ui/dashboard/v2",
    "expects": {
      "output": {"city": "string"},
      "input": {"temp": "number", "humid": "number"}
    }
  },
  "id": 3
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

