# URI基準階層型エラーハンドリング設計

## 概要
URI基準でClaudeインスタンスを階層化し、各レベルで異なるエラーハンドリング戦略を適用する設計。

## 階層構造

```
/                                   # ルートClaude（ユーザー対話）
├── /projects/                      # プロジェクト管理レベル
│   ├── /projects/kuzu/            # KuzuDBプロジェクトルート
│   │   ├── /projects/kuzu/src/    # ソースコード担当
│   │   ├── /projects/kuzu/tests/  # テスト担当
│   │   └── /projects/kuzu/docs/   # ドキュメント担当
│   └── /projects/web/             # Webプロジェクトルート
└── /tools/                        # ツール管理レベル
```

## エラーハンドリングの変化

### 1. ルートレベル（/）
**役割**: ユーザー対話、プロジェクト間調整
**エラーハンドリング**:
```yaml
error_strategies:
  user_interaction:
    - pattern: "ambiguous_request"
      action: "clarify_with_user"
      graph_lookup: false
    
  delegation_failure:
    - pattern: "project_timeout"
      action: "retry_with_increased_timeout"
      graph_lookup: true
      fallback: "report_to_user"
```

### 2. プロジェクトルート（/projects/*/）
**役割**: プロジェクト内調整、グラフDB管理
**エラーハンドリング**:
```yaml
error_strategies:
  coordination:
    - pattern: "conflicting_changes"
      action: "merge_strategy_from_graph"
      graph_query: |
        MATCH (e:Error {type: 'conflict', project: $uri})
        -[:SOLVED_BY]->(s:Solution)
        RETURN s.strategy
    
  resource_management:
    - pattern: "memory_limit"
      action: "distribute_to_subdirs"
      graph_update: true
```

### 3. サブディレクトリレベル（/projects/*/*/）
**役割**: 特定タスク実行
**エラーハンドリング**:
```yaml
error_strategies:
  task_execution:
    - pattern: "test_failure"
      action: "analyze_and_fix"
      graph_lookup: true
      report_to: "parent_uri"
    
  code_quality:
    - pattern: "linting_error"
      action: "auto_fix_or_escalate"
      threshold: 3  # 3回失敗したら上位へ
```

## グラフDBスキーマ

```cypher
// ノード定義
CREATE (uri:URI {path: '/projects/kuzu/src', level: 3})
CREATE (error:Error {
  type: 'compilation_error',
  message: 'undefined symbol',
  occurred_at: timestamp()
})
CREATE (solution:Solution {
  strategy: 'add_import',
  success_rate: 0.85,
  code_snippet: 'use crate::module::Symbol;'
})

// リレーション定義
CREATE (uri)-[:ENCOUNTERED]->(error)
CREATE (error)-[:SOLVED_BY]->(solution)
CREATE (solution)-[:APPLIED_AT]->(uri)
```

## 実装の現実性

### グラフDB採用の利点
1. **パターン学習**: エラーと解決策の関係を自然に表現
2. **横断的検索**: 似たエラーを他プロジェクトから学習
3. **成功率追跡**: 解決策の効果を定量化

### シンプル実装との組み合わせ
```json
{
  "uri": "/projects/kuzu/src",
  "local_handlers": {
    "compilation_error": "check_imports_first"
  },
  "graph_fallback": true,
  "escalation_threshold": 3
}
```

## エラーフロー例

1. `/projects/kuzu/src/`でコンパイルエラー発生
2. ローカルハンドラで`check_imports_first`実行
3. 解決しない場合、グラフDBクエリ:
   ```cypher
   MATCH (e:Error {type: 'compilation_error'})
   -[:SOLVED_BY]->(s:Solution)
   WHERE s.success_rate > 0.7
   RETURN s ORDER BY s.success_rate DESC LIMIT 3
   ```
4. 解決策適用、結果をグラフDBに記録
5. 3回失敗したら`/projects/kuzu/`へエスカレート

## プロンプト管理

各URIレベルでプロンプトテンプレート:
```yaml
/projects/kuzu/:
  base_prompt: |
    You are managing the KuzuDB project.
    Error handling priority: compilation > test > documentation
  
  error_context_injection: |
    Recent similar errors in this project:
    {{graph_query_results}}
```

## 実装優先順位

1. **Phase 1**: シンプルなURI階層とローカルハンドラ
2. **Phase 2**: グラフDB統合（読み取り専用）
3. **Phase 3**: 学習機能（グラフDB書き込み）
4. **Phase 4**: クロスプロジェクト学習

この設計により、各Claudeは自律的にエラーを処理しつつ、必要に応じて階層的にエスカレートし、過去の解決策から学習できる。