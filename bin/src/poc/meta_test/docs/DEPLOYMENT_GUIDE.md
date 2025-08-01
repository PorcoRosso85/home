# メタテストシステム導入ガイド

## 事前準備

### 1. 要件グラフの構築
```cypher
// requirement/graphに要件を登録
CREATE (r:RequirementEntity {
    id: 'req_your_feature',
    title: '機能名',
    description: '詳細説明',
    status: 'active'
});
```

### 2. テストエンティティの作成
```cypher
// 既存のテストをグラフに登録
CREATE (t:TestEntity {
    id: 'test_your_feature',
    name: 'テスト名',
    test_type: 'unit',  // unit, integration, e2e
    file_path: 'tests/test_your_feature.py'
});

// 要件と紐付け
MATCH (r:RequirementEntity {id: 'req_your_feature'})
MATCH (t:TestEntity {id: 'test_your_feature'})
CREATE (r)-[:VERIFIED_BY {
    verification_type: 'behavior',
    coverage_score: 0.8
}]->(t);
```

### 3. ビジネスメトリクスの定義
```cypher
// ビジネス指標を定義（例：API応答時間）
CREATE (m:BusinessMetric {
    id: 'api_response_time_20240201',
    metric_name: 'api_response_time',
    timestamp: '2024-02-01T00:00:00Z',
    value: 250,  // ミリ秒
    unit: 'ms'
});

// 要件との関連付け
MATCH (r:RequirementEntity {id: 'req_your_feature'})
MATCH (m:BusinessMetric {metric_name: 'api_response_time'})
CREATE (r)-[:IMPACTS {
    impact_type: 'performance',
    correlation_strength: 0.0  // 初期値、学習で更新
}]->(m);
```

## 自動化のためのツール

### 1. テスト自動登録スクリプト
```python
# scripts/auto_register_tests.py
import ast
import os
from pathlib import Path

def scan_test_files(test_dir: str):
    """テストファイルをスキャンして自動登録"""
    for test_file in Path(test_dir).glob("**/test_*.py"):
        with open(test_file) as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # テスト関数を発見
                yield {
                    "file": str(test_file),
                    "function": node.name,
                    "docstring": ast.get_docstring(node)
                }

def register_tests_to_graph(tests, graph_adapter):
    """テストをグラフDBに登録"""
    for test in tests:
        # テストエンティティを作成
        cypher = f"""
        CREATE (t:TestEntity {{
            id: '{test["function"]}',
            name: '{test["function"]}',
            description: '{test["docstring"] or ""}',
            file_path: '{test["file"]}',
            test_type: 'unit'
        }})
        """
        graph_adapter.execute_cypher(cypher)
```

### 2. CI/CD統合
```yaml
# .github/workflows/meta_test.yml
name: Meta Test Analysis

on:
  push:
    branches: [main, dev]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup KuzuDB
        run: |
          # KuzuDBセットアップ
          
      - name: Load Requirements
        run: |
          # requirement/graphをロード
          
      - name: Register Tests
        run: |
          python scripts/auto_register_tests.py
          
      - name: Run Test Executions
        run: |
          pytest --meta-test-export
          
      - name: Calculate Metrics
        run: |
          nix run .#calculate -- --all-requirements
          
      - name: Generate Report
        run: |
          nix run .#suggest -- --format=markdown > test_quality_report.md
```

### 3. ダッシュボード用データエクスポート
```python
# scripts/export_metrics.py
def export_metrics_to_json(graph_adapter, output_file: str):
    """メトリクスをJSON形式でエクスポート"""
    query = """
    MATCH (r:RequirementEntity)-[:HAS_METRIC]->(m:MetricResult)
    WHERE m.is_current = true
    RETURN r.id, r.title, 
           collect({
               metric: m.metric_name,
               score: m.score,
               details: m.details
           }) as metrics
    """
    
    results = graph_adapter.execute_cypher(query)
    
    dashboard_data = {
        "timestamp": datetime.now().isoformat(),
        "requirements": []
    }
    
    for row in results:
        dashboard_data["requirements"].append({
            "id": row["r.id"],
            "title": row["r.title"],
            "metrics": row["metrics"],
            "overall_score": calculate_overall_score(row["metrics"])
        })
    
    with open(output_file, "w") as f:
        json.dump(dashboard_data, f, indent=2)
```

## 段階的導入アプローチ

### Phase 1: 基礎構築（1-2週間）
1. requirement/graphへの要件登録
2. 主要テストの手動登録
3. 基本メトリクス（existence, reachability）の計算

### Phase 2: 自動化（2-4週間）
1. テスト自動登録スクリプトの導入
2. CI/CDパイプラインへの統合
3. 日次メトリクス計算の自動化

### Phase 3: ビジネス価値連携（1-2ヶ月）
1. ビジネスメトリクスの収集開始
2. インシデント管理システムとの連携
3. 学習ベースメトリクス（6,7）の活用

### Phase 4: 最適化（継続的）
1. メトリクス閾値の調整
2. ROIダッシュボードの構築
3. テスト改善の自動提案

## トラブルシューティング

### よくある問題

1. **テストが見つからない**
   - file_pathが正しいか確認
   - test_type（unit/integration/e2e）を確認

2. **メトリクスが低い**
   - VERIFIED_BY関係が正しく設定されているか
   - coverage_scoreが適切か

3. **学習が進まない**
   - TestExecutionデータが蓄積されているか
   - BusinessMetricが定期的に更新されているか