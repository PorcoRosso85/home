# Analytics Automation POC

## 目的

このディレクトリは以下の目的で作成されています：

- **Google Analytics**: トラッキングコードの自動導入と設定
- **Microsoft Clarity**: ヒートマップ・セッション録画ツールの自動導入
- **Infrastructure as Code (IaC)**: 必要に応じたインフラの自動構築

## 概要

ウェブサイトへのアナリティクスツール導入を半自動化し、手動設定の手間を削減します。

## 主要機能

### 1. Google Analytics自動導入
- GA4トラッキングコードの自動生成
- 適切な位置へのスクリプト挿入
- イベントトラッキングの基本設定

### 2. Microsoft Clarity自動導入  
- Clarityスクリプトの自動生成
- プロジェクトIDの管理
- プライバシー設定の適用

### 3. Infrastructure as Code
- 必要に応じたインフラリソースの定義
- 環境別設定の管理
- デプロイメントの自動化

## 使用方法

```bash
nix develop
# 実装予定
```

## ステータス

🚧 **開発中** - 基本構造の構築段階

## 関連ドキュメント

- `/home/nixos/bin/docs/conventions/` - 開発規約
- 各種アナリティクスツールの公式ドキュメント