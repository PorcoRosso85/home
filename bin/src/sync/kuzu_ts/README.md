# KuzuDB TypeScript Sync Platform

## 概要

PostgreSQL中央サーバーの課題を解決する、分散OLAP同期永続化プラットフォーム。

このプロジェクトは`poc/sync/unified`から移行され、本番環境での使用を前提とした実装です。

## 責務

- **分散OLAP同期基盤**
  - PostgreSQL中央集権モデルを分散型で代替
  - マルチマスター同期による単一障害点の排除

- **Immutableモデルの課題解決**
  - ストレージ爆発問題への対応（圧縮・アーカイブ）
  - GDPR準拠（論理/物理削除）
  - クエリ性能最適化

- **本番環境対応**
  - エンタープライズグレードの信頼性
  - 自動スケーリングと障害回復

## アーキテクチャ

```
従来: Client → PostgreSQL中央 → Client（単一ボトルネック）
新規: Client → Local KuzuDB → Unified Sync → Other KuzuDBs（分散協調）
```

### 実装済み機能 ✅
- マルチマスター同期（全ノードが書き込み可能）
- イベントソーシング（append-onlyモデル）
- 自動再接続（指数バックオフ）
- WebSocketリアルタイム通信

### 実装予定機能 🔄
1. **優先度1: 生存必須要件**
   - イベント圧縮（70%削減）
   - S3アーカイブ（30日以上）
   - GDPR対応（削除機能）
   - クエリキャッシュ（O(1)アクセス）

2. **優先度2: 運用必須要件**
   - 監視・アラート
   - バックアップ・リストア

## テスト実行方法

以下のコマンドでE2E/統合テストを実行できます：

```bash
nix run .#test
```

### テスト構成

- **E2Eテスト**: Python/pytest (`tests/e2e_test.py`)
  - KuzuDBインスタンス間の同期機能の完全な動作検証
  - エンドツーエンドのシナリオテスト

- **統合テスト**: TypeScript/Deno (`tests/integration.test.ts`)
  - コンポーネント間の連携テスト
  - API統合テスト

- **再接続テスト**: TypeScript/Deno (`tests/reconnection.test.ts`)
  - 自動再接続機能の検証
  - 障害回復シナリオ

## ドキュメント

- [MIGRATION_PLAN.md](./docs/MIGRATION_PLAN.md) - POCからの移行計画と背景
- [IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md) - 詳細な実装ロードマップ
- [discuss.md](./docs/discuss.md) - PostgreSQL vs KuzuDB詳細比較と課題分析

## 期待される効果

- **ストレージコスト**: 月100万円 → 3万円（97%削減）
- **法的リスク**: GDPR違反最大96億円 → ゼロ
- **クエリ性能**: 500ms → 1ms（500倍高速化）
- **可用性**: 99.99%（単一障害点なし）

## 開発環境

- **Nix Flakes**: 再現可能な開発環境
- **TypeScript/Deno**: サーバー実装
- **Python**: E2Eテスト
- **KuzuDB**: グラフデータベース