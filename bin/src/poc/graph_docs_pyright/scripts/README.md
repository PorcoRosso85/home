# Scripts Directory

このディレクトリは**実験的なスクリプト**を含みます。

## 責務の分離

### scripts/ (このディレクトリ)
- **目的**: 開発時の実験・検証
- **利用者**: 開発者のみ
- **安定性**: 保証なし、破壊的変更あり

### CLIコマンド (`python -m graph_docs`)
- **目的**: 正式なユーザーインターフェース
- **利用者**: エンドユーザー
- **安定性**: 後方互換性を維持

## 含まれるスクリプト

- `simple_analyze.py` - 基本的な解析（フィルタリングなし）のシンプルなラッパー
- `filtered_analyze.py` - 外部依存関係をフィルタリングする解析のラッパー

これらのスクリプトは、CLIハンドラー (`AnalyzeHandler`) を直接呼び出すシンプルなラッパーとして実装されています。

### 使用方法

```bash
# 基本的な解析（フィルタリングなし）
python scripts/simple_analyze.py /path/to/project [output_directory]

# フィルタリング付き解析（外部依存関係を除外）
python scripts/filtered_analyze.py /path/to/project [output_directory]
```

## 実装詳細

両スクリプトは以下の共通構造を持ちます：
1. `graph_docs.infrastructure.cli.analyze_handler.AnalyzeHandler` をインポート
2. コマンドライン引数を解析
3. `handler.analyze_with_filter()` を適切なパラメータで呼び出し
4. 結果を表示

主な違いは `filter_external` パラメータ：
- `simple_analyze.py`: `filter_external=False`（全ての診断を含む）
- `filtered_analyze.py`: `filter_external=True`（外部依存関係を除外）

## 注意

**エンドユーザーはこれらのスクリプトを直接使用すべきではありません。**
代わりに以下を使用してください：

```bash
# 正式なCLIコマンド（デフォルトでフィルタリング有効）
python -m graph_docs analyze /path/to/project

# フィルタリングを無効にする場合
python -m graph_docs analyze /path/to/project --no-filter
```