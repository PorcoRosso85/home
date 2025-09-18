# Meta-Test System

A system for evaluating test quality using 7 independent metrics, providing continuous learning and improvement capabilities through bi-directional integration with requirement graphs.

## Overview

The Meta-Test System analyzes test suites to ensure they effectively validate requirements and provide business value. It uses 7 independent metrics to measure different aspects of test quality while enriching the requirement graph with quality insights and discovered specifications.

## 7 Independent Metrics

1. **existence** - Test existence rate (percentage of requirements with tests)
2. **reachability** - Reachability (executable without circular references)
3. **boundary_coverage** - Boundary value coverage (testing thresholds)
4. **change_sensitivity** - Change sensitivity (fails when requirements change)
5. **semantic_alignment** - Semantic alignment (similarity between requirements and test descriptions)
6. **runtime_correlation** - Runtime correlation (correlation between test success and operational metrics)
7. **value_probability** - Value contribution probability (probability of contributing to business goals)

## Architecture

The system follows Domain-Driven Design (DDD) principles with clear separation of concerns:

```
meta_test/
├── domain/           # Business logic and metrics
├── application/      # Use cases and orchestration
├── infrastructure/   # External integrations
└── e2e/             # End-to-end tests
```

## Installation

```bash
# As a library (not yet published to PyPI)
pip install -e /path/to/meta_test

# Dependencies
pip install kuzu pydantic numpy httpx aiofiles
```

## Usage

### As a Library

```python
from meta_test.application import MetricsCalculator, ImprovementSuggestionGenerator
from meta_test.infrastructure import GraphAdapter

# Initialize with your requirement graph
adapter = GraphAdapter(db_path="/path/to/requirement_graph.db")
calculator = MetricsCalculator(adapter)

# Calculate all metrics for a requirement
metrics = calculator.calculate_all_metrics("req_001")
print(f"Test existence: {metrics['existence'].score}")
print(f"Boundary coverage: {metrics['boundary_coverage'].score}")

# Get improvement suggestions
generator = ImprovementSuggestionGenerator(threshold=0.7)
suggestions = generator.generate_suggestions({"req_001": metrics})
for suggestion in suggestions[:3]:  # Top 3
    print(f"{suggestion.metric_name}: {suggestion.suggestions}")

# Enrich requirement graph with quality insights
adapter.enrich_requirement(
    requirement_id="req_001",
    quality_metrics=metrics,
    discovered_specs=["30 second timeout", "5 retry limit"]
)

# Identify requirements that need clarification
ambiguous_reqs = calculator.find_low_semantic_alignment(threshold=0.5)
for req in ambiguous_reqs:
    print(f"Requirement {req.id} needs clearer specification")
```

### Output Format

```python
# MetricResult structure
{
    "requirement_id": "req_001",
    "metric_name": "existence",
    "score": 0.67,  # 0.0 to 1.0
    "details": {"total_requirements": 3, "tested": 2},
    "suggestions": ["Add test for sub-requirement req_001_c"]
}

# Error handling
from meta_test.infrastructure.result_types import DatabaseError
result = calculator.calculate_metric("existence", "req_001")
if isinstance(result, DatabaseError):
    print(f"Error: {result['message']}")
```

### Environment Variables

```bash
# KuzuDB connection
export META_TEST_DB_PATH="/path/to/requirement_graph.db"

# Logging configuration
export META_TEST_LOG_LEVEL="INFO"  # TRACE, DEBUG, INFO, WARN, ERROR
export LOG_FORMAT="json"  # or "console" (default)
```

### Installation

```bash
# Enter development environment
nix develop

# Or use direnv
direnv allow
```

### Commands

```bash
# Initialize the system
nix run .#init

# Calculate all metrics for a requirement
nix run .#calculate -- --requirement-id req_001

# Check specific metrics
nix run .#check -- existence
nix run .#check -- boundary_coverage

# Get improvement suggestions
nix run .#suggest -- --threshold 0.7

# Run learning process (for metrics 6 & 7)
nix run .#learn
```

### Testing

```bash
# Run all tests
nix run .#test

# Run specific test file
nix run .#test -- tests/test_existence.py

# Run with coverage
nix run .#test -- --cov=meta_test
```

### Development Tools

```bash
# Format code
nix run .#format

# Run linter
nix run .#lint

# Type check
nix run .#typecheck
```

## Bi-directional Integration with requirement/graph

### Forward Flow: Requirements → Test Quality
The system evaluates how well tests cover and validate requirements:
- Analyzes test coverage for each requirement
- Measures test effectiveness against specifications
- Identifies gaps in test suites

### Reverse Flow: Test Quality → Requirement Enhancement
The system enriches the requirement graph with insights from test analysis:
- **Implicit Requirement Discovery**: Extracts undocumented specifications from test implementations
- **Requirement Quality Feedback**: Identifies ambiguous or hard-to-test requirements
- **Metadata Enrichment**: Adds quality metrics, test history, and discovered constraints to requirement nodes

### Continuous Improvement Cycle
```
requirement/graph ←→ meta_test ←→ tests
     ↓                    ↓           ↓
specifications      quality metrics   execution
     ↑                    ↓           ↓
 enrichment ← insights ← analysis ← results
```

## Data Flow

```
requirement/graph (existing requirements graph)
         ↓
    7 metrics parallel calculation
         ↓
    Improvement suggestions generation
         ↓
Runtime data collection (metrics 6,7 only)
         ↓
    Learning updates
         ↓
  Cypher file persistence
         ↓
    GraphDB reflection
         ↓
Requirement graph enrichment (quality metadata)
```

## Design Principles

1. **No categorization** - The 7 metrics exist independently without grouping
2. **Independent responsibilities** - Each metric measures a unique aspect that others cannot
3. **Limited learning** - Only metrics 6 and 7 that require runtime data are learning targets
4. **Cypher persistence** - All data changes are recorded as Cypher files
5. **Reuse existing assets** - Leverages requirement/graph schema and data
6. **Bi-directional value** - Not just evaluating tests, but improving requirement quality
7. **Graph enrichment** - Accumulates metadata without modifying core requirements

## Extension

To add a new evaluation aspect:
1. Prove it cannot be expressed by existing 7 metrics
2. Add as 8th metric in domain/metrics/
3. No need to redefine or categorize existing metrics

## Q&A

### Q: 改善するテストはどうやって特定される？
A: 各指標に0.7（70%）の閾値を設定し、閾値未満のテストを改善対象として特定します。例えば、boundary_coverage = 0.4 の場合、「境界値テストが不足」として検出されます。

### Q: ビジネス価値の優先順位付けは誰が行う？
A: ビジネス価値（例：100万円削減）は**外部から与えられる前提**です。このシステムはビジネス価値を定義せず、テストとビジネス価値の**相関を測定**することに専念します。

### Q: 優先順位付けの基準は？
A: Impact（影響度）× Effort（工数）のマトリクスで判定します：
- **Quick Wins**: 高インパクト × 低工数（例：テスト追加、説明文更新）
- **Critical**: インパクト最大、工数不問（例：テストゼロ、実行不可）

### Q: 「継続的」とは具体的に何を指す？
A: 日次学習サイクルによるベイズ更新を指します：
- Day 1: runtime_correlation = 0.5（初期推定）
- Day 7: runtime_correlation = 0.65（実績で更新）
- Day 30: runtime_correlation = 0.72（収束）

cronで`nix run .#learn`を日次実行、またはCIでテスト後に自動更新されます。

### Q: 可視化機能はある？
A: 現在は数値での出力のみです。可視化は将来の拡張として検討可能ですが、現時点ではスコープ外です。

### Q: 既存のCIに統合するには？
A: CI環境でKuzuDBへの接続を設定し、`python -m meta_test calculate`を実行します。閾値未満で非ゼロ終了するため、CIのチェックとして使用できます。

### Q: パフォーマンスはどの程度？
A: 7つの指標は並列計算されます。1000要件規模で約10秒程度（KuzuDBのクエリ性能に依存）。

### Q: カスタム指標を追加するには？
A: `domain/metrics/`に新しいメトリクスクラスを追加し、`BaseMetric`を継承して`calculate`メソッドを実装します。既存7指標で表現できないことを先に確認してください。

### Q: 要件グラフはどのように充実していく？
A: meta_testは要件グラフを以下の3つの方法で充実させます：
1. **メタデータ追加**: 各要件に品質スコア、測定履歴、改善提案を付与
2. **暗黙的仕様の発見**: テストコードから制約条件や仕様を抽出して要件に追加
3. **関連性の発見**: テストと要件の相関から、文書化されていない依存関係を検出

### Q: 要件自体は変更される？
A: コア要件は変更せず、以下の層で管理します：
- **不変層**: 要件の本質的な意図（例：「ユーザー認証を提供」）
- **進化層**: 具体的な仕様（例：「30秒タイムアウト」）- テストから発見された内容で更新
- **メタデータ層**: 品質指標、実行履歴、相関データ - 継続的に蓄積