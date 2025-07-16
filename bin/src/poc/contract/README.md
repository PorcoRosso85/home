# Contract Service POC

自動契約締結サービスのPOC実装 - JSON Schemaさえあれば異なるサービス間で自動的に通信可能になる

## 問題と解決

### 問題
- 各POC/機能を独立して並列開発したい
- あとから統合を考えたくない（各々の責務を全うするだけでいい）
- 異なるPythonバージョン、異なる言語間での連携が困難
- `python -m`などの言語依存の実装に合わせたくない

### 解決
- **契約（JSON Schema）を持っていれば自動で通信可能**
- Consumerは「自分の情報を送る」だけ
- Providerを意識する必要なし
- 変換は自動化される

## コンセプト

```
Consumer「私はこういうデータ形式で送ります」
    ↓
Contract Service「了解。適切なProviderを探して変換します」
    ↓
Provider「私はこういうデータ形式で受け取ります」
    ↓
Contract Service「変換して届けました。結果も変換して返します」
    ↓
Consumer「自分の形式で結果を受け取りました！」
```

## アーキテクチャ

### グラフDBによる契約管理
```cypher
// Provider登録
(p:Provider {uri: "poc/search#run"})
  -[:PROVIDES]->(schema:Schema {
    input: {query: string, limit: integer},
    output: {results: array}
  })

// Consumer登録  
(c:Consumer {uri: "requirement/graph"})
  -[:EXPECTS]->(schema:Schema {
    output: {search_text: string, max_results: integer}
  })

// 自動マッチング
(c)-[:CAN_CALL]->(p) // 互換性があれば自動接続
```

### 主要機能

1. **契約登録**
   - Provider: 「こういう入力でこういう出力を返せます」
   - Consumer: 「こういう出力を送ります」
   - 両方JSON Schemaで宣言

2. **自動マッチング**
   - スキーマの互換性をグラフDBで判定
   - 型が一致または変換可能なら接続

3. **動的データ変換**
   ```javascript
   // 変換スクリプトも登録可能（DB保存）
   function transform(input) {
     return {
       query: input.search_text,
       limit: input.max_results || 10
     };
   }
   ```

4. **安全な実行**
   - Deno Workerで隔離実行
   - 権限なしで変換のみ許可

## 使用例

### Provider側
```typescript
// poc/search/contract.yaml
provider:
  uri: "poc/search#run"
  schema:
    input: 
      type: object
      properties:
        query: { type: string }
        limit: { type: integer }
    output:
      type: object
      properties:
        results: { type: array }
```

### Consumer側
```typescript
// requirement/graph/main.ts
const result = await contract.call({
  from: "requirement/graph",
  data: {
    search_text: "ユーザー認証",
    max_results: 5
  }
});
// 自動的にpoc/searchが呼ばれ、結果が返る
```

### 契約登録API
```typescript
// POST /register/provider
{
  "uri": "poc/weather#forecast",
  "schema": {
    "output": {
      "temperature": "number",
      "humidity": "number"
    }
  }
}

// POST /register/consumer
{
  "uri": "dashboard/widget",
  "expects": {
    "input": {
      "temp": "number",
      "humid": "number" 
    }
  }
}
```

## 技術スタック

- **Deno**: TypeScript実行環境、セキュリティ（Worker隔離）
- **KuzuDB**: グラフDB（契約関係の永続化、高速マッチング）
- **JSON Schema**: 契約定義の標準
- **JavaScript**: 変換スクリプト（動的実行）

## セキュリティ

- 変換スクリプトはWorkerで完全隔離
- ネットワーク・ファイルアクセス権限なし
- CPU/メモリ制限可能
- 入力検証は自動実施

## ディレクトリ構成

```
poc/contract/
├── README.md
├── flake.nix            # Nix環境定義
├── deno.json            # Denoタスク定義
├── src/
│   ├── main.ts          # HTTPサーバー
│   ├── registry.ts      # 契約登録・管理
│   ├── matcher.ts       # 契約マッチング 
│   ├── transformer.ts   # データ変換実行
│   ├── router.ts        # ルーティング
│   └── kuzu_wrapper.ts  # KuzuDB接続
├── test/
│   ├── fixtures/        # テスト用契約
│   └── integration/     # 統合テスト
└── examples/
    ├── simple/          # 基本的な例
    └── transform/       # 変換スクリプト例
```

## 将来の拡張

- WebSocket対応（リアルタイム通信）
- 契約バージョニング
- 変換パフォーマンス最適化（キャッシュ、事前コンパイル）
- 可視化ダッシュボード（誰と誰が繋がっているか）

## 開発開始

```bash
cd poc/contract
nix develop
deno task dev  # http://localhost:8000
```

## テスト

```bash
# 単体テスト
deno task test

# 統合テスト（実際のProvider/Consumer）
deno task test:integration
```