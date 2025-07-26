# テスト構造とその意味

## 概要

このドキュメントは、KuzuDB TypeScript Sync Platformのテストスイートの構造と、各テストの本質的意味を説明します。

## テストの分類

### 🌟 本質的テスト（Essential Tests）

システムの中核機能を検証する、削除不可能なテストです。

| テストファイル | 検証内容 | 本質的意味 |
|--------------|---------|-----------|
| **integration.test.ts** | WebSocket接続、イベント同期、複数クライアント | 分散同期の中核機能 |
| **reconnection.test.ts** | 自動再接続、クライアントID維持 | 分散環境での信頼性保証 |
| **e2e_test.py** | サーバー起動から同期までの全体フロー | システム全体の動作保証 |
| **event_group.test.ts** | 複数イベントの原子的操作 | トランザクション相当機能 |
| **transaction_manager.test.ts** | KuzuDBトランザクション統合 | ACID保証 |
| **compression.test.ts** | イベント圧縮による70%削減 | ストレージ爆発問題の解決 |
| **logical_delete.test.ts** | GDPR対応の論理削除 | 法的要件への対応 |

### 🔧 最適化テスト（Optimization Tests）

パフォーマンスを向上させるが、なくても基本機能は動作するテストです。

| テストファイル | 検証内容 | 意味 |
|--------------|---------|------|
| **aggregate_cache.test.ts** | 集計キャッシュのO(1)アクセス | OLAPパフォーマンス最適化 |
| **state_cache.test.ts** | 最新状態のキャッシュ | クエリ性能向上 |
| **vector_clock.test.ts** | 分散環境での因果関係追跡 | 高度な分散一貫性 |

### 📋 仕様テスト（Specification Tests）

将来実装予定の機能を文書化するテストです。

| テストファイル | 内容 | 目的 |
|--------------|------|------|
| **future_features.test.ts** | 18個のスキップテスト | 将来機能の仕様書として機能 |

## 削除されたテスト

以下のテストは本質的意味が薄いため削除されました：

- ~~characterization.test.ts~~ - 既存動作の記録（開発補助）
- ~~performance_cache.test.ts~~ - パフォーマンス測定（ベンチマーク）
- ~~transactional_sync_adapter.test.ts~~ - 実装詳細（統合テストで十分）
- ~~transactional_integration.test.ts~~ - 実装詳細（他のテストでカバー）

## テスト実行

```bash
# すべての本質的テストを実行
nix run .#test

# 個別カテゴリのテスト実行
deno test tests/integration.test.ts  # 分散同期
deno test tests/compression.test.ts  # ストレージ最適化
pytest tests/e2e_test.py            # E2Eテスト
```

## メンテナンスガイドライン

1. **新しいテストを追加する前に**：
   - そのテストは本質的機能を検証するか？
   - 既存のテストでカバーできないか？
   - 実装詳細ではなく振る舞いを検証しているか？

2. **テストの削除基準**：
   - 他のテストと重複している
   - 実装の詳細をテストしている
   - ビジネス価値に直結しない

3. **テストの移動**：
   - パフォーマンステストは別リポジトリへ
   - 開発支援テストはCIから除外