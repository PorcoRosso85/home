# Qwen-Code Flake Integration

## 責務 (Responsibilities)

このflakeの責務は、[Qwen-Code](https://github.com/QwenLM/qwen-code)リポジトリをNixで使用可能にすることです。

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

## Flake実装の目標

1. **依存関係管理**: Node.js v20+環境の提供
2. **パッケージ化**: `@qwen-code/qwen-code`のNixパッケージ作成
3. **開発環境**: 開発者向けのNix開発シェル提供
4. **設定管理**: API設定の適切な管理方法の提供

## インストール方法（通常）

```bash
# npmグローバルインストール
npm install -g @qwen-code/qwen-code@latest

# ソースからのインストール
git clone https://github.com/QwenLM/qwen-code
cd qwen-code
npm install
```

## Nix Flakeでの提供予定

- `packages.qwen-code`: メインパッケージ
- `devShells.default`: 開発環境
- `apps.qwen-code`: 実行可能アプリケーション