# CozoDB Time Travel API

CozoDB を使用した Time Travel 機能に関する実装例です。この実装では、特定時点のデータ取得や異なる時点間のデータ比較などの機能を提供します。

## 概要

CozoDB は強力なデータベースですが、そのTime Travel機能（Validity期間）をNode.jsやDenoで活用できます。この実装例では、その機能を使って Time Travel を簡単に実現するための機能を提供します。

## 主な機能

- 特定時点のデータを取得する機能
- 異なる時点間のデータの変更履歴を取得する機能
- 特定時点から別の時点へのデータの変更を比較する機能
- データの履歴全体を取得する機能

## 実行方法

### Node.js での実行

```bash
# 基本実装の実行
node working_time_travel.js

# 高度な関数の実行
node --experimental-strip-types cozoTimeTravelFunctions.ts
```

### Deno での実行

このプロジェクトのTypeScriptコードはDenoでも実行できます。ただし、cozo-nodeのネイティブバインディングが必要とする`libstdc++.so.6`へのパスを環境変数に設定する必要があります。

```bash
# 環境変数を設定してDenoで実行
LD_LIBRARY_PATH=/nix/store/2y8c3b7ydkl68liz336035llfhmm6r95-gfortran-14-20241116-lib/lib/ nix run nixpkgs#deno -- run --allow-all cozoBasicOperations.ts

# あるいは複数のファイルを実行するためのショートカットスクリプト
LD_LIBRARY_PATH=/nix/store/2y8c3b7ydkl68liz336035llfhmm6r95-gfortran-14-20241116-lib/lib/ nix run nixpkgs#deno -- run --allow-all cozoTimeTravel.ts
```

#### Deno実行上の注意点

1. **必要なシステムライブラリ**:
   - Node.jsのネイティブモジュールである`cozo-node`を使用するには、`libstdc++.so.6`が必要です
   - NixOSでは上記のパスに存在します（環境によって異なる場合があります）

2. **モジュールインポートの互換性**:
   - 複数のファイルを参照するコードでは、インポートパスの拡張子（`.ts`または`.js`）に注意が必要です
   - Denoでは拡張子を明示的に指定する必要があります

3. **実行権限**:
   - `--allow-all`フラグをつけることで、ファイルシステムやネットワークなどへのアクセス権限を付与しています

## ファイル構成

- **time_travel_guide.md** - CozoDB でのTime Travel機能に関する説明書
- **cozoTimeTravelFunctions.ts** - Time Travel を実現するための高レベル関数ライブラリ
- **working_time_travel.js** - シンプルな実装例（JavaScript版）
- **test_report.md** - テスト結果報告
- **conclusion.md** - テスト結論と今後の可能性
- **interface/cli.ts** - コマンドラインインターフェース
- **application/timeTravel/api.ts** - アプリケーション層の実装
- **domain/timeTravel/service.ts** - ドメインロジック
- **infrastructure/timeTravel/repository.ts** - インフラ層の実装

## 簡単な使用例

### 基本実装の例

```javascript
import { CozoDb } from "cozo-node";

// データベース初期化
const db = new CozoDb();

// リレーション作成
await db.run(`
  :create user_status {
    uid: String,
    ts: String =>
    mood: String
  }
`);

// データ挿入
await db.run(`?[uid, mood] <- [["alice", "happy"]] :put user_status {uid, ts: "2023-01-01T00:00:00Z" => mood}`);
await db.run(`?[uid, mood] <- [["alice", "excited"]] :put user_status {uid, ts: "2023-06-01T00:00:00Z" => mood}`);

// 特定時点のデータ取得
const targetDate = "2023-03-01T00:00:00Z";
const pastData = await db.run(`
  latest_ts[uid, max(ts)] := *user_status{uid, ts}, ts <= "${targetDate}"
  ?[uid, mood] := latest_ts[uid, ts], *user_status{uid, ts, mood}
`);

// 最新データ取得
const latestData = await db.run(`
  latest_ts[uid, max(ts)] := *user_status{uid, ts}
  ?[uid, mood] := latest_ts[uid, ts], *user_status{uid, ts, mood}
`);
```

## 注意事項

- この実装例はCozo-node v0.7.6以上で動作します
- Cozo-nodeのValidity機能の詳細については公式ドキュメントを参照してください
- 高レベル関数を使用することで、より簡潔で保守性の高いコードが書けます
