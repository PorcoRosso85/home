# X.com Developer API 接続実証

## 責務
このディレクトリは、X.com (旧Twitter) Developer APIへの接続実証を行うPOC（Proof of Concept）を管理します。

## 目的
- X.com Developer APIとの接続方法の検証
- 認証フローの実装と動作確認
- APIレスポンスの取得と処理の実証
- 実用化に向けた技術的課題の洗い出し

## スコープ
- OAuth 2.0認証の実装
- 基本的なAPIエンドポイントへのアクセス検証
- レート制限への対応方法の確認
- エラーハンドリングのパターン検証

## 成果物
- API接続のサンプルコード
- 認証フローの実装例
- APIレスポンスの処理例
- 実装時の注意点・課題のドキュメント

## 使用方法

### ツイート取得
```bash
# Bearer tokenを使用（X Developer Portalから取得）
X_BEARER_TOKEN=your_token bun run src/cli.ts <tweet_id>
```

## テスト実行

### 通常のテスト
```bash
bun test
```

### E2Eテスト（実際のAPI呼び出し）
```bash
# Bearer tokenを使用（X Developer Portalから取得）
REAL_API_TEST=true X_BEARER_TOKEN=your_token bun test test/e2e/real_api.spec.ts
```

**注意**: E2Eテストは実際のAPIを呼び出すため、レート制限とAPI使用料金が発生します。`REAL_API_TEST=true`を設定しない限り自動的にスキップされます。