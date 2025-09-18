# Nix開発環境

Nix言語開発のための統合環境（LSP、フォーマッター、Linter）を提供します。

## 基本的な使い方

ヘルプを表示: `nix run .`

## 推奨コマンド（標準Nixインターフェース）

```bash
# コードフォーマット実行
nix fmt

# 全ての品質チェックを実行
nix flake check
```

## 高度なチェック

### 個別品質チェック

```bash
# フォーマットチェックのみ
nix build .#checks.x86_64-linux.format

# Lintチェックのみ  
nix build .#checks.x86_64-linux.lint
```

### CI/CD連携

この flake は標準的な `formatter` と `checks` 出力を提供しており、CI/CDシステムで自動品質チェックが可能です：

- **フォーマッター**: `nix fmt` で統一的なコードフォーマット
- **フォーマットチェック**: `nixfmt` による統一的なコードフォーマット検証
- **Lintチェック**: `statix` および `deadnix` による静的解析

### チェック内容

1. **フォーマットチェック (`format`)**
   - 全ての `.nix` ファイルが `nixfmt` の規則に従っているかチェック
   - 不正なフォーマットがある場合はビルドが失敗

2. **Lintチェック (`lint`)**
   - `statix`: Nixアンチパターンの検出
   - `deadnix`: 未使用コードの検出
   - 警告やエラーがある場合はビルドが失敗

## 移行ガイド

従来のコマンドから標準インターフェースへの移行：

| 旧コマンド | 新コマンド | 説明 |
|-----------|-----------|------|
| `nix run .#format` | `nix fmt` | 標準フォーマットコマンド |
| `nix run .#check` | `nix flake check` | 標準品質チェックコマンド |
| `nix run .#lint` | `nix build .#checks.<system>.lint` | 個別リントチェック |

### レガシーサポート

互換性のため、従来のコマンドも引き続き使用可能ですが、非推奨メッセージが表示されます：

```bash
# 非推奨（互換性のため利用可能）
nix run .#format   # → 自動的に nix fmt を実行
nix run .#check    # → 自動的に nix flake check を実行
nix run .#lint     # → 個別リント実行（直接実行も可能）
```