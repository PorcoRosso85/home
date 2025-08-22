# KuzuDB Modular Graph Architecture

## 概要
KuzuDBを使用した、複数グラフ情報の統合・連結を可能にするモジュラーアーキテクチャの実装。

## アーキテクチャ目標

### 1. KuzuDB基盤
- **依存**: `bin/src/persistence/kuzu`のKuzuDB実装を基盤として使用
- **データベース**: グラフデータベースとしてKuzuDBを採用
- **永続化層**: 既存のpersistence層との統合

### 2. モジュラーグラフ設計

#### 2.1 継承元グラフ (Base Graph)
- **役割**: 共通のスキーマ・データ構造を定義
- **責務**:
  - 基本的なノード・エッジタイプの定義
  - 共通プロパティの管理
  - データ整合性の保証
- **特徴**:
  - 再利用可能な基盤グラフ
  - 拡張可能なスキーマ設計
  - バージョン管理対応

#### 2.2 継承先グラフ (Derived Graph)
- **役割**: ユースケース固有の拡張グラフ
- **責務**:
  - 継承元グラフの一部情報を選択的に連結
  - ユースケース固有のプロパティ追加
  - 特定ドメインへの最適化
- **特徴**:
  - 継承元からの選択的データ参照
  - 独自拡張の自由度
  - パフォーマンス最適化

### 3. グラフ連結機能

#### 3.1 統合メカニズム
```
┌─────────────────┐
│   Base Graph    │
│  (継承元グラフ)  │
└────────┬────────┘
         │継承・参照
    ┌────┴────┬──────────┐
    ↓         ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐
│Graph A │ │Graph B │ │Graph C │
│(UseCase│ │(UseCase│ │(UseCase│
│   A)   │ │   B)   │ │   C)   │
└────────┘ └────────┘ └────────┘
```

#### 3.2 連結方式
- **スキーマ継承**: 継承元グラフのスキーマを基に拡張
- **データ参照**: 必要なデータのみを選択的に参照
- **レイジーローディング**: 実際に必要になるまでデータ読み込みを遅延
- **キャッシング**: 頻繁にアクセスされるデータの最適化

### 4. 実装構成

#### 4.1 ディレクトリ構造
```
kuzu_modularize/
├── flake.nix           # Nixパッケージ定義
├── README.md           # このファイル
├── base/               # 継承元グラフ実装
│   ├── schema/         # スキーマ定義
│   ├── migrations/     # マイグレーション
│   └── core.cypher     # 基本クエリ
├── derived/            # 継承先グラフ実装群
│   ├── use_case_a/     # ユースケースA固有
│   ├── use_case_b/     # ユースケースB固有
│   └── use_case_c/     # ユースケースC固有
├── connectors/         # グラフ間連結ロジック
│   ├── inheritance.py  # 継承メカニズム
│   └── linker.py       # データ連結
└── tests/              # テストスイート
    ├── unit/           # 単体テスト
    └── integration/    # 統合テスト
```

#### 4.2 主要コンポーネント
1. **BaseGraphManager**: 継承元グラフの管理
2. **DerivedGraphBuilder**: 継承先グラフの構築
3. **GraphLinker**: グラフ間の連結処理
4. **SchemaInheritance**: スキーマ継承メカニズム
5. **QueryOptimizer**: クロスグラフクエリの最適化

### 5. 利用例

#### 5.1 継承元グラフの定義
```python
base_graph = BaseGraphManager()
base_graph.define_schema({
    "nodes": {
        "Person": {"name": "STRING", "age": "INT32"},
        "Organization": {"name": "STRING", "type": "STRING"}
    },
    "edges": {
        "WORKS_FOR": {"from": "Person", "to": "Organization"}
    }
})
```

#### 5.2 継承先グラフの作成
```python
derived_graph = DerivedGraphBuilder(base_graph)
derived_graph.select_entities(["Person", "WORKS_FOR"])
derived_graph.extend_schema({
    "Person": {"department": "STRING", "salary": "DOUBLE"}
})
```

#### 5.3 グラフ間連結
```python
linker = GraphLinker()
linker.connect(base_graph, derived_graph)
result = linker.query_across_graphs("""
    MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)
    WHERE p.department = 'Engineering'
    RETURN p.name, o.name
""")
```

## 技術スタック
- **データベース**: KuzuDB
- **言語**: Python/TypeScript (bin/src/persistence/kuzu互換)
- **パッケージ管理**: Nix Flakes
- **テスト**: pytest/Deno test

## 開発状況
- [ ] flake.nix設定
- [ ] 継承元グラフ基盤実装
- [ ] 継承先グラフビルダー
- [ ] グラフ連結メカニズム
- [ ] クエリ最適化
- [ ] テストスイート
- [ ] ドキュメント整備

## 参考資料
- [KuzuDB公式ドキュメント](https://kuzudb.com/docs/)
- `bin/src/persistence/kuzu_py/`: Python実装参考
- `bin/src/persistence/kuzu_ts/`: TypeScript実装参考