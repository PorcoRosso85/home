# AIChat ツール拡張ガイド

このドキュメントでは、AIChat システム用の新しいツールを作成、ビルド、探索する方法を説明します。

## 目次

1. [概要](#概要)
2. [ツールの追加方法](#ツールの追加方法)
3. [ツール作成補助](#ツール作成補助)
4. [ツールの探索](#ツールの探索)
5. [開発ベストプラクティス](#開発ベストプラクティス)

## 概要

AIChat システムは Function Calling / MCP プロトコルを使用して拡張可能です。これにより、新しいツールを作成して AIChat の機能を拡張できます。主な拡張メカニズムには次のものがあります：

- **ツールの追加**: `tools.txt` ファイルを編集して新しいツールを登録
- **ツール作成補助**: `extension_assistant.sh` でツール作成のサポートを受ける
- **ツール探索**: `extension_search.sh` で既存のツールを検索・分析

## ツールの追加方法

### ステップ1: ツールを作成する

新しいツールを作成するには、`tools` ディレクトリに `.sh`、`.py`、または `.js` ファイルを作成します。

```bash
# 例: tools ディレクトリに新しいシェルスクリプトツールを作成
touch tools/my_new_tool.sh
chmod +x tools/my_new_tool.sh
```

### ステップ2: ツールコードを実装する

ツールには適切な形式のヘッダーコメントが必要です：

```bash
#!/usr/bin/env bash
set -e

# @describe ツールの説明を入力します
# @option --parameter パラメータの説明
# @flag --feature フラグの説明

# ツールのコード...

eval "$(argc --argc-eval "$0" "$@")"
```

### ステップ3: tools.txt に追加する

作成したツールを `tools.txt` に追加して登録します：

```bash
# tools.txt に新しいツールを追加
echo "my_new_tool.sh" >> tools.txt
```

### ステップ4: ツールをビルドする

最後に、ツールをビルドして AIChat システムに認識させます：

```bash
# カレントディレクトリが aichat_extension であることを確認
cd /path/to/aichat_extension

# ツールをビルド
argc build

# 問題がないか確認
argc check
```

## ツール作成補助

`extension_assistant.sh` ツールは、新しいツールの作成プロセスをサポートします。

### 使用方法

```bash
extension_assistant --language [bash|python|javascript] [--show_examples]
```

### パラメータ

- `--language`: ツールを作成する言語を指定 (bash, python, javascript)
- `--show_examples`: (オプション) 各言語のサンプルコードを表示

### 例

```bash
# Bash でのツール作成方法と例を表示
extension_assistant --language bash --show_examples

# Python でのツール作成の基本情報を取得
extension_assistant --language python
```

### 機能

- 各言語に応じたツール作成のガイドラインを提供
- タグの使い方や構文に関する情報を提供
- オプションパラメータやフラグの定義方法を説明
- サンプルコードを提供（`--show_examples` フラグ使用時）

## ツールの探索

`extension_search.sh` ツールを使用して、既存のツールを検索・分析できます。

### 使用方法

```bash
extension_search --pattern "検索文字列" [オプション]
```

### パラメータ

- `--pattern`: 検索するテキストパターン（正規表現使用可）
- `--path`: 検索対象のディレクトリパス（デフォルト: カレントディレクトリ）
- `--file-pattern`: 検索対象のファイルパターン（例: "*.sh", "*.{js,ts}"）
- `--case-sensitive`: 大文字と小文字を区別する（フラグ）
- `--only-filenames`: ファイル名のみを表示する（フラグ）
- `--fuzzy`: ファジーマッチングを有効にする（文字間に任意文字を許容）
- `--show-help`: マッチしたファイルの -h/--help 出力も表示する

### 例

```bash
# 全ツールから "search" を含むものを検索
extension_search --pattern "search" --path "/home/nixos/bin/src/aichat_extension/tools" --file-pattern "*.sh"

# 大文字小文字を区別せず "API" を検索
extension_search --pattern "API" --case-sensitive

# 正確なスペルがわからない場合のファジー検索
extension_search --pattern "weathr" --fuzzy

# マッチしたファイルのヘルプ情報も表示
extension_search --pattern "search" --show-help
```

### 機能

- テキストパターンに基づくファイル内容の検索
- ファイルタイプによるフィルタリング
- 大文字小文字を区別するオプション
- ファイル名のみの表示機能
- ファジーマッチング機能（正確なスペルがわからない場合に便利）
- ヘルプ情報の表示機能（マッチしたファイルの使い方を確認）

## 開発ベストプラクティス

### ツール命名規則

- わかりやすい名前を使用する（例: `search_wikipedia.sh`, `get_current_weather.sh`）
- 複数の単語はアンダースコア（`_`）で区切る
- ファイル拡張子は言語に合わせる（`.sh`, `.py`, `.js`）

### ドキュメンテーション

- 必ず `@describe` タグでツールの目的と使用法を説明する
- 各パラメータに対して明確な説明を提供する
- 必要に応じてコード内にコメントを追加する

### エラーハンドリング

- ユーザー入力の検証を行う
- わかりやすいエラーメッセージを提供する
- 適切な終了コードを返す

### セキュリティ

- 信頼性の低い入力は適切にサニタイズする
- 機密情報は環境変数として管理し、直接コードに記述しない
- 必要最小限の権限でツールを実行する

---

このドキュメントは、AIChat システムのツール拡張機能に関する基本的なガイドです。より詳細な情報や最新の変更については、開発チームに問い合わせるか、関連するドキュメントを参照してください。
