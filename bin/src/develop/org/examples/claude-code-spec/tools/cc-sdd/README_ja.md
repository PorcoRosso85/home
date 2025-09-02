# cc-sdd

✨ **Claude Code/Gemini CLIをプロトタイプからプロダクション対応開発プロセスへ**

<!-- npm badges -->
[![npm version](https://img.shields.io/npm/v/cc-sdd?logo=npm)](https://www.npmjs.com/package/cc-sdd?activeTab=readme)
[![npm downloads](https://img.shields.io/npm/dm/cc-sdd?logo=npm)](https://www.npmjs.com/package/cc-sdd)
[![install size](https://packagephobia.com/badge?p=cc-sdd)](https://packagephobia.com/result?p=cc-sdd)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<div align="center"><sub>
<a href="https://github.com/gotalab/claude-code-spec/blob/main/tools/cc-sdd/README.md">English</a> | 日本語 | <a href="https://github.com/gotalab/claude-code-spec/blob/main/tools/cc-sdd/README_zh-TW.md">繁體中文</a>
</sub></div>

Claude CodeとGemini CLIを **AI-DLC (AI駆動開発ライフサイクル)**へ。**AIネイティブプロセス**と**最小限の人間承認ゲート**：AIが実行を駆動し、人間が各フェーズで重要な決定を検証。

🎯 **最適な用途**: 従来開発の70%オーバーヘッド（会議・文書・儀式）から脱却し、AIネイティブ実行と人間品質ゲートで **週単位から時間単位の納期** を実現。

> **Kiro互換** — プロフェッショナル環境で実証済みの同じワークフロー。

## 🚀 インストール

```bash
# 基本インストール（デフォルト: 英語ドキュメント、Claude Codeエージェント）
npx cc-sdd@latest

# 言語オプション（デフォルト: --lang en）
npx cc-sdd@latest --lang ja    # 日本語
npx cc-sdd@latest --lang zh-TW # 繁体字中国語

# エージェントオプション（デフォルト: claude-code）
npx cc-sdd@latest --gemini-cli --lang ja # Gemini CLI用
```

## ✨ クイックデモ

```bash
# AIエージェント起動: 'claude' または 'gemini'

# AI-DLCコアパターンの実践：
/kiro:spec-init ユーザー認証システムをOAuthで構築  # AIが計画作成
/kiro:spec-requirements auth-system                  # AIが明確化のための質問
/kiro:spec-design auth-system                       # 人間が検証、AIが実装
/kiro:spec-tasks auth-system                        # 繰り返し: 計画→質問→検証→実装
```

**30秒セットアップ** → **AI駆動「ボルト」（スプリントではなく）** → **時間単位の結果**

## ✨ 主要機能

- **🚀 AI-DLC手法** - 人間承認付きAIネイティブプロセス。コアパターン：AI実行、人間検証
- **📋 仕様ファースト開発** - 包括的仕様を単一情報源としてライフサイクル全体を駆動
- **⚡ 「ボルト」（スプリントではなく）** - 週単位ではなく時間・日単位サイクル。70%の管理オーバーヘッドから脱却
- **🧠 プロジェクトメモリ** - AIがセッション間で永続的コンテキストを維持、パターンを学習
- **🔄 AIネイティブ+人間ゲート** - AI計画 → AI質問 → 人間検証 → AI実装（品質管理付き高速サイクル）
- **🌍 チーム対応** - 品質ゲート付き多言語・クロスプラットフォーム・標準化ワークフロー

## 🤖 対応AIエージェント

| エージェント | 状態 | コマンド | 設定 |
|-------|--------|----------|--------|
| **Claude Code** | ✅ 完全対応 | 8スラッシュコマンド | `CLAUDE.md` |
| **Gemini CLI** | ✅ 完全対応 | 8コマンド | `GEMINI.md` |
| その他 | 📅 予定 | - | - |
 
## 📋 コアコマンド

### 開発ワークフロー
```bash
/kiro:spec-init <description>             # 機能仕様を初期化
/kiro:spec-requirements <feature_name>    # 要件を生成
/kiro:spec-design <feature_name>          # 技術設計を作成  
/kiro:spec-tasks <feature_name>           # 実装タスクに分解
/kiro:spec-impl <feature_name> <tasks>    # TDDで実行
/kiro:spec-status <feature_name>          # 進捗を確認
```

### プロジェクトセットアップ
```bash
/kiro:steering                            # プロジェクトメモリを作成/更新
/kiro:steering-custom                     # カスタム指導ルール
```

## ⚙️ 設定

```bash
# 言語とプラットフォーム
npx cc-sdd@latest --lang ja --os mac   # macOS
npx cc-sdd@latest --lang ja --os linux # Linux（macテンプレートを共有）
npx cc-sdd@latest --lang ja --os windows # Windows（専用テンプレート）

# 安全な操作  
npx cc-sdd@latest --dry-run --backup

# カスタムディレクトリ
npx cc-sdd@latest --kiro-dir docs/specs
```

## 📁 プロジェクト構造

インストール後、プロジェクトに以下が追加されます：

```
project/
├── .claude/commands/kiro/    # 8つのスラッシュコマンド
├── .kiro/specs/             # 機能仕様書
├── .kiro/steering/          # AI指導ルール
└── CLAUDE.md                # プロジェクト設定
```

## 📚 ドキュメント & サポート

- **[完全ドキュメント](https://github.com/gotalab/claude-code-spec/blob/main/README.md)** - 完全セットアップガイド
- **[コマンドリファレンス](https://github.com/gotalab/claude-code-spec/docs)** - すべてのオプションと例  
- **[問題 & サポート](https://github.com/gotalab/claude-code-spec/issues)** - バグ報告と質問
- **[Kiro IDE統合](https://kiro.dev)** - 拡張仕様管理

---

**ベータリリース** - 使用可能、改善中。[問題を報告](https://github.com/gotalab/claude-code-spec/issues) | MIT License

### プラットフォーム対応
- 対応OS: macOS / Linux / Windows（通常は自動検出）。
- Linux は macOS と同じコマンドテンプレートを使用します。Windows は専用テンプレートを使用します。
