# graph_docs_pyright

Pyright Language Server Protocolを使用した型認識コード解析ツール。KuzuDBグラフデータベースによる永続化機能付き。

## 目的

- Pyright Language Server Protocol (LSP) を使って指定ディレクトリ配下の全関数・シンボルを取得
- 型情報を含む詳細なシンボル情報を抽出
- KuzuDBにnodeとして永続化
- 型を考慮した依存関係をrelationとして永続化

## ctagsとの違い

### ctags版 (graph_docs)
- 構文解析ベースでシンボルを抽出
- 基本的なシンボル情報（名前、種類、位置）のみ
- 型情報なし
- 単純な呼び出し関係の検出

### Pyright版 (このプロジェクト)
- 型解析エンジンを使用した高精度な解析
- 完全な型情報（引数の型、返り値の型、ジェネリクス）
- 型推論による暗黙的な依存関係の検出
- インポート関係、継承関係、実装関係の正確な把握
- 未使用コード、型エラーの検出

## 技術スタック

- **Pyright**: TypeScript/JavaScript/Pythonの型チェッカー（LSP経由で使用）
- **KuzuDB**: グラフデータベースとして関数・シンボルと依存関係を永続化
- **Python**: メイン実装言語
- **LSP (Language Server Protocol)**: Pyrightとの通信プロトコル

## データ構造

### Node: Symbol
- **location_uri**: シンボルの位置を表すURI（例: `file:///path/to/file.py#L10`）
- **name**: シンボル名
- **kind**: シンボルの種類（function, class, method, variable など）
- **type_info**: 型情報（JSON形式）
  - **parameters**: パラメータの型情報
  - **return_type**: 返り値の型
  - **generics**: ジェネリクス情報
- **scope**: スコープ情報（モジュール、クラス、関数）
- **signature**: 完全なシグネチャ
- **docstring**: ドキュメンテーション文字列
- **is_exported**: エクスポートされているか
- **is_abstract**: 抽象メソッド/クラスか

### Relationship: CALLS
- Symbol間の呼び出し関係を表現
- from_symbol -[CALLS]-> to_symbol
- **line_number**: 呼び出しが発生した行番号
- **call_type**: 呼び出しの種類（direct, method, constructor）
- **is_type_safe**: 型安全な呼び出しか

### Relationship: IMPORTS
- モジュール間のインポート関係
- from_module -[IMPORTS]-> to_module
- **import_type**: インポートの種類（import, from_import）
- **imported_names**: インポートされた名前のリスト

### Relationship: INHERITS
- クラスの継承関係
- child_class -[INHERITS]-> parent_class
- **inheritance_type**: 継承の種類（extends, implements）

### Relationship: REFERENCES
- 型参照関係（型注釈での使用など）
- symbol -[REFERENCES]-> type_symbol
- **reference_type**: 参照の種類（parameter, return, variable）

## 実装アプローチ

### 1. Pyright LSPクライアントの実装

```python
from pyright_lsp import PyrightLSPClient

class PyrightAnalyzer:
    def __init__(self):
        self.client = PyrightLSPClient()
    
    async def analyze_project(self, project_path: str):
        # プロジェクトを開く
        await self.client.initialize(project_path)
        
        # 全ファイルのシンボル情報を取得
        symbols = await self.client.get_workspace_symbols()
        
        # 各シンボルの詳細情報を取得
        for symbol in symbols:
            # 型情報を取得
            type_info = await self.client.get_symbol_type(symbol)
            # 参照を取得
            references = await self.client.find_references(symbol)
            # 定義を取得
            definition = await self.client.go_to_definition(symbol)
```

### 2. KuzuDBスキーマの拡張

```cypher
// 型情報を含むSymbolノード
CREATE NODE TABLE Symbol(
    location_uri STRING PRIMARY KEY,
    name STRING,
    kind STRING,
    type_info STRING,  // JSON形式の型情報
    scope STRING,
    signature STRING,
    docstring STRING,
    is_exported BOOLEAN,
    is_abstract BOOLEAN
)

// 型参照関係
CREATE REL TABLE REFERENCES(
    FROM Symbol TO Symbol,
    reference_type STRING,
    line_number INT64
)

// インポート関係
CREATE REL TABLE IMPORTS(
    FROM Symbol TO Symbol,
    import_type STRING,
    imported_names STRING[]
)

// 継承関係
CREATE REL TABLE INHERITS(
    FROM Symbol TO Symbol,
    inheritance_type STRING
)
```

### 3. 高度な分析機能

```python
class TypeAwareAnalyzer:
    def find_type_errors(self):
        """型エラーがあるコードを検出"""
        pass
    
    def find_unused_types(self):
        """未使用の型定義を検出"""
        pass
    
    def analyze_type_coverage(self):
        """型カバレッジを分析"""
        pass
    
    def find_any_usage(self):
        """Any型の使用箇所を検出"""
        pass
    
    def suggest_type_improvements(self):
        """型定義の改善提案"""
        pass
```

## 使用方法（予定）

```bash
# ディレクトリを指定して解析
nix run .#analyze /path/to/project

# 型エラーチェック付き解析
nix run .#analyze /path/to/project --check-types

# 特定の言語のみ解析
nix run .#analyze /path/to/project --language python

# 分析結果をエクスポート
nix run .#analyze /path/to/project --export-dir ./output
```

## 期待される成果

1. **正確な依存関係グラフ**: 型情報を含む完全な依存関係
2. **型安全性の可視化**: どの呼び出しが型安全でどれが危険かを明示
3. **リファクタリング支援**: 型情報に基づく安全なリファクタリング提案
4. **デッドコード検出の精度向上**: 型情報を考慮したより正確な未使用コード検出
5. **アーキテクチャ分析**: 型の依存関係からアーキテクチャの問題を検出

## 実装ステップ

1. Pyright LSPクライアントの基本実装
2. シンボル情報の取得とパース
3. KuzuDBスキーマの定義と基本的な永続化
4. 型情報の抽出と永続化
5. 関係（CALLS, IMPORTS, INHERITS, REFERENCES）の検出と永続化
6. 分析クエリの実装
7. CLIインターフェースの実装
8. Nixパッケージ化

## 技術的課題

- Pyright LSPサーバーの起動と管理
- 大規模プロジェクトでのパフォーマンス
- 型情報の正規化とグラフ構造への変換
- 言語間の差異の吸収（Python, TypeScript, JavaScript）

## ctagsベースのgraph_docsからの移行価値

### 現状の課題（ctags版）
- 型情報が取得できない
- 動的な呼び出しを追跡できない
- ジェネリクスや型パラメータを理解できない
- インターフェースと実装の関係が不明確

### Pyright版で解決される問題
- **完全な型情報**: 引数、返り値、ジェネリクスを含む
- **型推論の活用**: 明示的でない型も推論により取得
- **より正確な参照解決**: 型情報を使った正確な参照解決
- **クロスファイル分析**: プロジェクト全体の型フローを理解

## サンプルクエリ（予定）

### 型安全性の分析
```cypher
// Any型を使用している関数を検出
MATCH (s:Symbol)
WHERE s.kind = 'function' 
  AND s.type_info CONTAINS '"Any"'
RETURN s.name, s.location_uri

// 型エラーの可能性がある呼び出しを検出
MATCH (a:Symbol)-[c:CALLS]->(b:Symbol)
WHERE c.is_type_safe = false
RETURN a.name, b.name, c.line_number
```

### アーキテクチャ分析
```cypher
// 循環的な型依存を検出
MATCH p = (a:Symbol)-[:REFERENCES*]->(a)
WHERE LENGTH(p) > 1
RETURN p

// 最も多くの型から参照されているインターフェース
MATCH (s:Symbol)<-[r:REFERENCES]-()
WHERE s.kind = 'interface'
RETURN s.name, COUNT(r) as ref_count
ORDER BY ref_count DESC
```