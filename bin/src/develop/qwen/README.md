# Qwen-Code Nix Wrapper

## 責務 (Responsibilities)

このディレクトリは、[Qwen-Code](https://github.com/QwenLM/qwen-code)をnixpkgsから実行するシンプルなラッパーを提供します。

## 概要

Qwen-Codeは、開発者向けのAI駆動型コマンドラインツールで、コーディングワークフローを強化するために設計されています。Qwen3-Coder AIモデルに最適化されており、Google's Gemini CLIから派生したものです。

## 主な機能

- 大規模コードベースの探索と分析
- 開発タスクの自動化
- インテリジェントなコード支援
- 高度なコード編集とリファクタリング

## 技術要件

- **Node.js**: バージョン20以上が必要
- **API統合**: 複数のプロバイダーとの設定可能なAPI統合
- **無料APIティア**: ModelScopeとOpenRouterからサポート

## 実装方式

このディレクトリは最小限の実装を提供します：
- `qwen-code.sh`: nixpkgsから`qwen-code`を直接実行するシェルスクリプト
- `flake.nix`: 空のflake（互換性のため維持）
- OpenRouter APIのデフォルト設定を内蔵

## 使用方法

### 1. 直接実行（推奨）

```bash
# OpenRouter APIキーがスクリプトに設定済みの場合
./qwen-code.sh

# 環境変数でカスタマイズする場合
OPENAI_API_KEY="your-key" OPENAI_MODEL="qwen/qwen3-235b-a22b:free" ./qwen-code.sh
```

### 2. 環境変数の設定

`qwen-code.sh`にはデフォルトのOpenRouter設定が含まれています：
- `OPENAI_API_KEY`: OpenRouter APIキー
- `OPENAI_BASE_URL`: `https://openrouter.ai/api/v1`
- `OPENAI_MODEL`: `qwen/qwen3-coder`

これらは環境変数で上書き可能です。`.env.example`を参考にしてください。

### 3. OpenRouterの利用

[OpenRouter](https://openrouter.ai/)に$10以上デポジットすると、無料モデル（*-free）を1日1000リクエストまで使用できます。

詳細は`docs/`ディレクトリ内の記事を参照してください。

## 内部動作

`qwen-code.sh`スクリプトは以下を実行します：
1. OpenRouter API設定を環境変数として設定
2. `nix shell nixpkgs#qwen-code`でqwen-codeを実行
3. すべての引数をqwen-codeに渡す

## 注意事項

- nixpkgsにqwen-codeパッケージが存在することが前提です
- 初回実行時はnixpkgsからのダウンロードが発生します
- API設定は環境変数で上書き可能です