# Contract-Flake-Nickel 実装仕様書

## アーキテクチャ設計

### 統合フロー
```
Producer Flake → JSON出力 → Consumer Flake
     ↓              ↓            ↓
契約準拠チェック → パイプ → 契約準拠チェック
```

### ディレクトリ構造
```
integration/
├── producer-flake/
│   └── flake.nix          # 独立したProducerプロジェクト
├── consumer-flake/
│   └── flake.nix          # 独立したConsumerプロジェクト
└── pipeline.sh            # 統合実行スクリプト
```

## 実装要件

### 1. integration/producer-flake/flake.nix
- **責務**: Nickel契約に準拠したデータ生成
- **出力形式**: JSON標準出力
- **契約**: ProducerContract準拠
- **実行方法**: `nix run .#default`

### 2. integration/consumer-flake/flake.nix  
- **責務**: Producer出力データの消費・処理
- **入力形式**: JSON標準入力
- **契約**: ConsumerContract準拠出力
- **実行方法**: `nix run .#default < input.json`

### 3. integration/pipeline.sh
- **責務**: Producer→Consumer完全パイプライン
- **機能**: 
  - Producer実行→Consumer実行のパイプ
  - エラーハンドリング
  - 契約違反検知

### 4. flake.nix更新
- **追加パッケージ**:
  - `producer-executable`: integration/producer-flake実行
  - `consumer-executable`: integration/consumer-flake実行

## データフロー設計

### ProducerContract出力例
```json
{
  "processed": 10,
  "failed": 2,
  "output": ["item-1", "item-2", "item-3"]
}
```

### ConsumerContract出力例
```json
{
  "summary": "Processed 10 items with 2 failures",
  "details": {
    "processed": 10,
    "failed": 2,
    "output": ["item-1", "item-2", "item-3"]
  }
}
```

## エラーハンドリング

### 契約違反パターン
1. **型不整合**: `processed`が文字列
2. **必須フィールド欠損**: `output`フィールドなし  
3. **不正な値**: `failed`が負数

### エラー処理方法
- Nickel型チェックでの事前検証
- パイプライン実行時の動的チェック
- 明確なエラーメッセージ出力

## テスト戦略

### 正常系テスト
- Producer→Consumerパイプライン成功
- 正しいJSON形式での受け渡し
- 契約準拠データの処理

### 異常系テスト  
- 契約違反データの拒否
- 不正JSON形式の処理
- パイプライン中断時の処理

## パフォーマンス要件
- パイプライン実行時間: 10秒以内
- メモリ使用量: 100MB以内
- 大量データ対応: 1000項目まで

## 成功基準
1. `nix run .#producer-executable | nix run .#consumer-executable`が成功
2. JSON形式でデータが正しく受け渡される
3. 契約違反データは適切に拒否される
4. エラーメッセージが明確に表示される
5. `nix flake check`が全てパスする