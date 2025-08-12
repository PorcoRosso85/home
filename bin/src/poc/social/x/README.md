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

## テスト方針

### モックレス・テスティング

本プロジェクトではモックを一切使用せず、以下の2層でテストを実施しています：

**テスト戦略**:
- **単体テスト**: ドメインロジックの純粋な振る舞い検証（モックなし）
- **E2Eテスト**: 実際のAPIとの連携動作確認（実環境）

**理由**:
- Bunのmock.module機能の不安定性
- 規約「モックは最小限のみ例外的に許可する」への準拠
- 実装詳細ではなく振る舞いをテストする原則の徹底

### E2Eテスト拡張計画

**拡張予定**:
- エラーケースのテストシナリオ追加
- レート制限処理の動作確認
- 異常系APIレスポンスのハンドリング検証

**品質担保**:
- 単体テスト: ロジック正当性の保証（35テスト）
- E2Eテスト: 実際のAPI連携動作の保証（3テスト）
- 統合テスト: 削除（モック使用による規約違反のため）