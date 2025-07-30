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

## Usage

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