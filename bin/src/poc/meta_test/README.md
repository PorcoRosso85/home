# Meta-Test System

A system for evaluating test quality using 7 independent metrics, providing continuous learning and improvement capabilities.

## Overview

The Meta-Test System analyzes test suites to ensure they effectively validate requirements and provide business value. It uses 7 independent metrics to measure different aspects of test quality.

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

# Custom threshold
generator_strict = ImprovementSuggestionGenerator(threshold=0.9)
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
```

## Design Principles

1. **No categorization** - The 7 metrics exist independently without grouping
2. **Independent responsibilities** - Each metric measures a unique aspect that others cannot
3. **Limited learning** - Only metrics 6 and 7 that require runtime data are learning targets
4. **Cypher persistence** - All data changes are recorded as Cypher files
5. **Reuse existing assets** - Leverages requirement/graph schema and data

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