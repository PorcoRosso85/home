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

## アーキテクチャ

本プロジェクトはDomain-Driven Design (DDD) に基づいて構成されています：

### ディレクトリ構造

```
graph_docs/
├── domain/           # ドメインモデル層
│   └── entities.py   # QueryResult, DualQueryResult などのエンティティ
├── application/      # アプリケーション層
│   ├── analyzer_service.py    # Pyright解析サービス
│   └── interfaces/
│       └── repository.py      # リポジトリインターフェース
├── infrastructure/   # インフラストラクチャ層
│   ├── cli/
│   │   └── cli_handler.py    # CLIハンドラー
│   ├── kuzu/
│   │   ├── kuzu_repository.py      # KuzuDBリポジトリ実装
│   │   └── dual_kuzu_repository.py # デュアルDBリポジトリ
│   └── pyright/      # Pyright関連（未実装）
├── pyright_client.py # Pyright LSPクライアント
├── pyright_analyzer.py # Pyright解析器
├── kuzu_storage.py   # KuzuStorage（後方互換性のため）
├── mod.py            # DualKuzuDB（後方互換性のため）
└── cli_display.py    # CLIディスプレイユーティリティ
```

### 1. Domain層

ビジネスロジックの中核となるエンティティを定義：

```python
# domain/entities.py
@dataclass
class QueryResult:
    """クエリ結果を表すエンティティ"""
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    timing: Optional[float] = None

@dataclass
class DualQueryResult:
    """デュアルクエリ結果を表すエンティティ"""
    local: Optional[QueryResult] = None
    server: Optional[QueryResult] = None
```

### 2. Application層

ビジネスロジックを実装し、ドメインとインフラストラクチャを繋ぐ：

```python
# application/analyzer_service.py
class AnalyzerService:
    def __init__(self, repository: IRepository):
        self.repository = repository
        self.analyzer = PyrightAnalyzer()
    
    def analyze_and_store(self, directory: str) -> Dict[str, Any]:
        results = self.analyzer.analyze_directory(directory)
        self.repository.store_analysis(results)
        return results
```

### 3. Infrastructure層

外部システムとの統合を担当：

```python
# infrastructure/kuzu/kuzu_repository.py
class KuzuRepository(IRepository):
    """KuzuDBを使用したリポジトリの実装"""
    def store_analysis(self, analysis_results: Dict[str, Any]) -> None:
        # KuzuDBへの保存ロジック
        pass
```

### DDDアーキテクチャの利点

1. **関心の分離**: 各層が明確な責務を持つ
2. **テスタビリティ**: インターフェースによる依存性の注入でテストが容易
3. **拡張性**: 新しいストレージやアナライザーの追加が簡単
4. **保守性**: ビジネスロジックが明確に分離されている

## KuzuDBスキーマ

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

## 実装完了内容

### 実装済み機能
1. ✅ **PyrightAnalyzer** - Pyright CLIでの型チェック
2. ✅ **KuzuStorage** - 解析結果のグラフDB保存
3. ✅ **統合テスト** - 型エラー検出とKuzuDB保存の検証
4. ✅ **COPY TO/FROM Parquet** - Parquet形式でのエクスポート/インポート
5. ✅ **永続化とデータ移行** - ファイルDB → Parquet → in-memory DBの完全なフロー
6. ✅ **DDDアーキテクチャ** - Domain/Application/Infrastructure層の分離
7. ✅ **リポジトリパターン** - KuzuRepositoryによるデータアクセス抽象化
8. ✅ **DualKuzuDB** - 2つのKuzuDBインスタンスを同時操作
9. ✅ **E2Eテスト** - ユーザー・製品・ソーシャルグラフのテスト

### KuzuStorage API

```python
# 基本機能
storage = KuzuStorage(":memory:")  # in-memory DB
storage = KuzuStorage("path/to/db.kuzu")  # 永続化DB

# データ保存
storage.store_analysis(pyright_results)

# クエリ
files_with_errors = storage.query_files_with_errors()

# Parquetエクスポート/インポート
storage.export_to_parquet("output/dir")  # files.parquet, diagnostics.parquet を生成
storage.import_from_parquet("input/dir")  # Parquetファイルからデータをインポート
```

### テスト実行

```bash
# 全テストを実行
nix run .#test

# 個別テスト
python test_minimal.py      # 基本的な解析とKuzuDB保存
python test_persistence.py  # 永続化、Parquet、データ移行
```
