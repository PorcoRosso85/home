# tags_in_dir

ctagsを使用してディレクトリ配下のコードベースを解析し、KuzuDBに永続化するツール。

## 目的

- ctagsを使って指定ディレクトリ配下の全関数・シンボルを取得
- KuzuDBにnodeとして永続化
- 依存関係をrelationとして永続化

## 技術スタック

- ctags: コード解析（Pythonサブプロセス経由）
- KuzuDB: グラフデータベースとして関数・シンボルと依存関係を永続化
- Python: メイン実装言語

## データ構造

### Node: Symbol
- **location_uri**: シンボルの位置を表すURI（例: `file:///path/to/file.py#L10`）
- **name**: シンボル名
- **kind**: シンボルの種類（function, class, method など）
- **scope**: スコープ情報（オプション）
- **signature**: シグネチャ（オプション）
- スキーマ付きパスのみを格納

### Relationship: CALLS
- Symbol間の呼び出し関係を表現
- from_symbol -[CALLS]-> to_symbol
- **line_number**: 呼び出しが発生した行番号（オプション）

## 使用方法

### 基本的な使用方法

```python
from tags_in_dir import CtagsParser
from kuzu_storage import KuzuStorage

# ctagsパーサーの初期化
parser = CtagsParser()

# KuzuDBストレージの初期化
storage = KuzuStorage(":memory:")  # または storage = KuzuStorage("path/to/db.kuzu")

# シンボルの抽出
symbols = parser.extract_symbols("/path/to/project", extensions=[".py"])

# KuzuDBに保存
storage.store_symbols(symbols)

# 関係の作成
storage.create_calls_relationship(
    "file:///path/to/file1.py#L10",
    "file:///path/to/file2.py#L20"
)
```

### クエリ例

```python
# ファイル内のシンボルを検索
symbols = storage.find_symbols_by_file("/path/to/file.py")

# 名前でシンボルを検索
symbols = storage.find_symbols_by_name("my_function")

# 種類でシンボルを検索
functions = storage.find_symbols_by_kind("function")

# Cypherクエリの実行
results = storage.execute_cypher("""
    MATCH (s:Symbol)
    WHERE s.location_uri CONTAINS 'file.py'
    RETURN s.name, s.kind
""")

# 呼び出し関係の検索
called_by, calling = storage.find_symbol_calls("file:///path/to/file.py#L10")
```

## テスト

```bash
# Nix環境でテストを実行
nix develop -c pytest test_kuzu_storage.py -v
nix develop -c pytest test_tags_in_dir.py -v

# または
nix run .#test
```

## 例

実際の使用例は `example_integration.py` を参照：

```bash
nix develop -c python example_integration.py .
```

## 高度な分析機能

### 呼び出し関係の自動検出

```python
from call_detector import CallDetector

# シンボル情報を使って呼び出し関係を検出
detector = CallDetector(symbol_dicts)
relationships = detector.detect_all_calls("/path/to/project", extensions=[".py"])

# 検出された関係をKuzuDBに保存
resolved_calls = detector.resolve_call_targets(relationships)
for from_uri, to_uri, line_no in resolved_calls:
    storage.create_calls_relationship(from_uri, to_uri, line_no)
```

### コード分析クエリ

```python
from analysis_queries import CodeAnalyzer

analyzer = CodeAnalyzer(storage)

# 1. ファイル内の全関数を検索
functions = analyzer.find_all_functions_in_file("/path/to/file.py")

# 2. 最も多く呼ばれている関数を検索
most_called = analyzer.find_most_called_functions(limit=10)

# 3. デッドコード（呼ばれていない関数）を検出
dead_code = analyzer.find_dead_code()

# 4. 循環依存を検出
cycles = analyzer.find_circular_dependencies(max_depth=5)

# 5. 関数の呼び出し階層を取得
hierarchy = analyzer.get_function_call_hierarchy("my_function", max_depth=3)

# 6. エントリーポイントを検索
entry_points = analyzer.find_entry_points()

# 7. ファイル間の依存関係を分析
dependencies = analyzer.get_file_dependencies("/path/to/file.py")

# 8. 複雑度メトリクスを取得
metrics = analyzer.get_complexity_metrics()
```

## Cypherクエリ例

### 基本的なクエリ

```cypher
// 全シンボルをカウント
MATCH (s:Symbol)
RETURN COUNT(s) AS total_symbols

// 種類別にシンボルをカウント
MATCH (s:Symbol)
RETURN s.kind, COUNT(s) AS count
ORDER BY count DESC

// 特定ファイル内の関数を検索
MATCH (s:Symbol)
WHERE s.location_uri STARTS WITH 'file:///path/to/file.py#'
  AND s.kind = 'function'
RETURN s.name, s.location_uri
ORDER BY s.location_uri
```

### 呼び出し関係の分析

```cypher
// 最も多く呼ばれている関数トップ10
MATCH (s:Symbol)<-[c:CALLS]-()
WHERE s.kind = 'function'
WITH s, COUNT(c) AS call_count
RETURN s.name, s.location_uri, call_count
ORDER BY call_count DESC
LIMIT 10

// デッドコード（呼ばれていない関数）
MATCH (s:Symbol)
WHERE s.kind = 'function'
  AND NOT EXISTS {
      MATCH (s)<-[:CALLS]-()
  }
  AND s.name != 'main'
  AND NOT s.name STARTS WITH 'test_'
RETURN s.name, s.location_uri

// 相互再帰（2つの関数が互いを呼び合う）
MATCH (a:Symbol)-[:CALLS]->(b:Symbol)-[:CALLS]->(a)
WHERE a.kind = 'function' AND b.kind = 'function'
  AND a.location_uri < b.location_uri
RETURN a.name AS func1, b.name AS func2

// 関数の呼び出しチェーン（3段階）
MATCH path = (a:Symbol)-[:CALLS]->(b:Symbol)-[:CALLS]->(c:Symbol)
WHERE a.kind = 'function' 
  AND b.kind = 'function' 
  AND c.kind = 'function'
RETURN a.name AS caller, b.name AS intermediate, c.name AS callee
LIMIT 10
```

### 複雑度の分析

```cypher
// 最も多くの関数を呼び出している関数（高結合度）
MATCH (s:Symbol)-[c:CALLS]->()
WHERE s.kind = 'function'
WITH s, COUNT(c) AS out_calls
RETURN s.name, out_calls
ORDER BY out_calls DESC
LIMIT 10

// ファイル間の依存関係
MATCH (from:Symbol)-[:CALLS]->(to:Symbol)
WHERE NOT from.location_uri STARTS WITH SUBSTRING(to.location_uri, 0, INDEXOF(to.location_uri, '#'))
WITH DISTINCT 
  SUBSTRING(from.location_uri, 7, INDEXOF(from.location_uri, '#') - 7) AS from_file,
  SUBSTRING(to.location_uri, 7, INDEXOF(to.location_uri, '#') - 7) AS to_file
RETURN from_file, to_file
ORDER BY from_file, to_file

// クラスとそのメソッド数
MATCH (s:Symbol)
WHERE s.kind = 'method' AND s.scope IS NOT NULL AND s.scope != ''
WITH s.scope AS class_name, COUNT(s) AS method_count
RETURN class_name, method_count
ORDER BY method_count DESC
```

### グラフ探索

```cypher
// 特定の関数から到達可能な全関数（推移的閉包）
MATCH (start:Symbol {name: 'main'})-[:CALLS*1..5]->(reached:Symbol)
WHERE start.kind = 'function' AND reached.kind = 'function'
RETURN DISTINCT reached.name, reached.location_uri

// 最短パスの検索
MATCH (from:Symbol {name: 'function_a'}), (to:Symbol {name: 'function_b'})
WHERE from.kind = 'function' AND to.kind = 'function'
MATCH path = shortestPath((from)-[:CALLS*]->(to))
RETURN path

// 強連結成分（相互に到達可能な関数グループ）
MATCH (a:Symbol)-[:CALLS*]->(b:Symbol)-[:CALLS*]->(a)
WHERE a.kind = 'function' AND b.kind = 'function'
WITH DISTINCT a
RETURN COLLECT(a.name) AS strongly_connected_functions
```

## 完全なワークフローのデモ

完全な分析ワークフローを確認するには：

```bash
# デモスクリプトを実行（現在のディレクトリを分析）
nix develop -c python demo_analysis.py .

# 永続的なデータベースを使用
nix develop -c python demo_analysis.py /path/to/project /tmp/analysis.kuzu
```

このデモスクリプトは以下を実行します：
1. ctagsでシンボルを抽出
2. 呼び出し関係を自動検出
3. KuzuDBにデータを保存
4. 様々な分析クエリを実行
5. 結果をレポート形式で表示