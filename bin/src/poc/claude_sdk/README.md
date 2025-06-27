# Claude SDK POC

Claude Code Max Subscriptionでの動作確認用POC（Python & TypeScript）

## 概要

このPOCは、Claude Code環境でAPIキー不要でClaude SDKを使用できることを確認するためのものです。

## Python POC

### セットアップ

```bash
cd bin/src/poc/claude_sdk
uv sync
```

### 実行方法

#### 基本的な使用例
```bash
uv run python main.py
```

#### 高度な使用例（ストリーミング、非同期、ツール使用）
```bash
uv run python advanced_example.py
```

#### Claude Code SDK経由のテスト
```bash
uv run python test_sdk_cli.py
```

## TypeScript POC

### 機能

1. ✅ **セッション継続機能** (--continueのような機能)
   - セッション履歴の保存・読み込み
   - コンテキストを保持した会話の継続

2. ✅ **リアルタイムstream-json解析**
   - ストリーミングレスポンスのリアルタイム処理
   - 文字単位での表示とパフォーマンス測定

3. ✅ **SDKへのリクエスト送信**
   - 柔軟なオプション設定
   - エラーハンドリングと中断制御

### セットアップ

```bash
cd bin/src/poc/claude_sdk
npm install
```

### 実行方法

#### 統合デモ（全機能）
```bash
npm start
```

#### ストリーミング特化デモ
```bash
npm run stream-demo
```

#### セッション管理デモ
```bash
npm run session-demo
```

### TypeScriptファイル構成

```
src/
├── main.ts         # 統合デモ（全機能実装）
├── stream-demo.ts  # ストリーミング特化デモ
└── session-demo.ts # セッション管理デモ
```

## 重要な発見

### Python
- 直接のAnthropic SDK: APIキーが必要（環境変数なしでは動作しない）
- Claude Code SDK: Claude Code CLI経由で動作し、APIキー不要（CLIが認証を処理）

### TypeScript
- `@anthropic-ai/claude-code`パッケージはCLIツールのみ
- SDKとして使用する場合も、内部でsubprocessを使ってCLIを呼び出す

### 結論
- どちらの言語でも、Claude Code使用時はCLI経由（subprocess）が必須
- APIキーなしでClaude Codeを使うには、CLI経由が唯一の方法