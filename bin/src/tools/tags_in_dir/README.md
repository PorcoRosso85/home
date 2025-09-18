# tags_in_dir

ctagsを使用してコードベースを解析し、KuzuDBにグラフとして永続化するツール。

## 目的

- ctagsでディレクトリ配下の全関数・シンボルを抽出
- KuzuDBにnodeとして永続化  
- 依存関係をrelationとして永続化
- Cypherクエリで高度な分析を実現

## アーキテクチャ

本ツールは規約に準拠した3層アーキテクチャで構成されています：

- **Domain層**: ビジネスロジック（純粋関数、外部依存なし）
- **Application層**: ユースケース（Domain層とInfrastructure層を調整）
- **Infrastructure層**: 外部システムとの統合（ctags、KuzuDB、ファイルシステム）

## 使用方法

### インストール

```bash
# 開発環境
nix develop /home/nixos/bin/src/tools/tags_in_dir

# 外部からの利用
inputs.tags-in-dir.url = "path:/home/nixos/bin/src/tools/tags_in_dir";
pythonEnv = tags-in-dir.packages.${system}.default;
```

### CLI使用例

```bash
# ディレクトリを解析
nix run /home/nixos/bin/src/tools/tags_in_dir -- /path/to/project

# findと組み合わせ
find -d 3 | nix run /home/nixos/bin/src/tools/tags_in_dir

# 分析結果をエクスポート
nix run /home/nixos/bin/src/tools/tags_in_dir -- /path/to/project --export-dir ./output
```

### ライブラリとしての使用

```python
from tags_in_dir import extract_symbols, analyze_codebase

# シンボル抽出
symbols = extract_symbols("/path/to/project")

# コードベース分析
results = analyze_codebase("/path/to/project")
```

## データ構造

### Node: Symbol
- **location_uri**: シンボルの位置URI（例: `file:///path/to/file.py#L10`）
- **name**: シンボル名
- **kind**: 種類（function、class、method等）

### Relationship: CALLS
- Symbol間の呼び出し関係
- **line_number**: 呼び出し箇所の行番号

## 分析機能

- デッドコード検出
- 循環依存検出
- 複雑度メトリクス
- ファイル依存関係分析

詳細なCypherクエリ例は[ドキュメント](./docs/queries.md)を参照。