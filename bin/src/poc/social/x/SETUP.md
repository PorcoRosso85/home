# X.com Developer API POC セットアップガイド

## 前提条件
- Nix環境がインストール済み
- X Developer Accountを保有
- Bearer Tokenを取得済み（X Developer Portal から）

## クイックスタート

### 1. 環境構築
```bash
# プロジェクトディレクトリへ移動
cd /home/nixos/bin/src/poc/social/x

# Nix開発環境に入る
nix develop

# 依存関係のインストール（初回のみ）
bun install
```

### 2. 認証設定

#### Bearer Token を設定
```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集してBearer Tokenを設定
echo "X_BEARER_TOKEN=your_bearer_token_here" > .env
```

**注意**: Bearer Token は X Developer Portal (https://developer.x.com/) から取得してください。

### 3. 動作確認

#### 基本的なテスト実行
```bash
# ユニットテストと統合テストを実行
bun test
```

#### 実際のAPIでテスト
```bash
# 実際のAPIを使用したE2Eテスト（要：有効な認証情報）
REAL_API_TEST=true bun test test/e2e/real_api.spec.ts
```

#### CLIでツイート取得
```bash
# ツイートIDを指定して取得
bun run src/cli.ts 20
```

## 認証方式
- `X_BEARER_TOKEN` のみサポート
- Bearer Token がない場合はエラー

## トラブルシューティング

### "Authentication credentials are required" エラー
- .envファイルが正しく作成されているか確認
- X_BEARER_TOKEN環境変数が正しく設定されているか確認
- `source .env` または新しいシェルセッションで再試行
- Bearer Token がX Developer Portalから正しく取得されているか確認

### "Rate limit exceeded" エラー
- Free プランの制限: 月100件の読み取り
- 15分間の制限を超えた場合は時間をおいて再試行

### テストが失敗する
```bash
# 環境変数を設定してテスト実行
export X_BEARER_TOKEN=test_token
bun test
```

## 開発のヒント

### テスト駆動開発
```bash
# ドメイン層のテストのみ実行
bun test test/domain

# 統合テストのみ実行
bun test test/integration
```

### モックを使用した開発
統合テストではネットワーク層のみモック化されているため、
実際のAPIなしでも開発可能です。

## API制限と料金

### Free プラン
- 月100件の読み取り（GET）
- 月500件の書き込み（POST）
- 基本的なv2エンドポイントのみ

### 推奨事項
- 開発時はモックを使用
- E2Eテストは必要最小限に
- レート制限を考慮した実装

## 関連ドキュメント
- [README.md](./README.md) - プロジェクト概要
- [BABY_STEPS.md](./BABY_STEPS.md) - 実装ステップ
- [TEST_REFACTORING_REPORT.md](./TEST_REFACTORING_REPORT.md) - テスト設計