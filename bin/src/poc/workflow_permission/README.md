# KuzuDB Workflow Permission System - TDD Red Phase

## 概要
組織の承認フローとロールベース認可をKuzuDBで実装するPOC。
TDD（テスト駆動開発）のRed Phase（失敗するテスト）から開始。

## テストスイート

### 1. 組織承認ワークフローテスト (7テスト)
- 組織階層の構築（部長→課長→担当者）
- 自動的な承認者設定
- 承認待ち一覧の取得
- 多段階承認（高優先度）
- 承認フローの状態遷移
- 全承認完了時の処理
- 却下時の処理

### 2. ロールベースアクセス制御テスト (8テスト)
- ロールの付与
- ロールベースの権限チェック
- 階層ロールの権限継承
- 所有者権限
- 部門ベースのアクセス制御
- 一時的な権限付与
- 権限の委任
- 権限取得経路の説明

## 実行方法

```bash
cd /home/nixos/bin/src/poc/workflow_permission
uv run pytest -v
```

## 現在の状態
- ✅ 15個の失敗するテストケースを作成
- ✅ `NotImplementedError`で全テストが失敗
- ✅ uv run pytestで実行可能

## 次のステップ
1. WorkflowPermissionSystemクラスの実装
2. KuzuDBのスキーマ設計
3. 各メソッドの実装
4. テストをグリーンにする