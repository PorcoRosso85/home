# Data-Driven Testing for Duplicate Detection

This directory contains YAML test data files for data-driven testing of the duplicate detection functionality.

## Benefits of Data-Driven Testing

1. **Separation of Concerns**: Test data is separated from test logic, making tests cleaner and more maintainable
2. **Easy Test Case Addition**: New test cases can be added without modifying code
3. **Better Visibility**: All test scenarios are clearly visible in one place
4. **Reusability**: Test data can be shared across different test implementations
5. **Version Control**: Changes to test data are tracked separately from code changes

## How to Add New Test Cases

### Level 1: Pure Business Rules
Add test cases under `test_level_1` in `duplicate_detection_cases.yaml`:

```yaml
similarity_cases:
  - name: "your_test_name"
    description: "What this test verifies"
    req1:
      id: "req_001"
      title: "Requirement Title"
      description: "Requirement Description"
    req2:
      id: "req_002"
      title: "Another Title"
      description: "Another Description"
    expected_similarity: 0.8  # Optional: exact similarity score
    min_similarity: 0.5       # Optional: minimum similarity
    max_similarity: 0.9       # Optional: maximum similarity
    expected_duplicate: true  # Optional: whether it's a duplicate
    threshold: 0.7           # Optional: threshold for duplicate detection
```

### Level 2: Mock Integration Tests
Add scenarios under `test_level_2`:

```yaml
integration_scenarios:
  - name: "scenario_name"
    description: "What this scenario tests"
    requirements:
      - id: "req_001"
        title: "First Requirement"
        description: "First Description"
        expect_warning: false
      - id: "req_002"
        title: "Similar Requirement"
        description: "Similar Description"
        expect_warning: true
        expected_duplicate_ids: ["req_001"]
```

### Level 3: End-to-End User Journeys
Add user journeys under `test_level_3`:

```yaml
user_journeys:
  - name: "journey_name"
    description: "User story being tested"
    steps:
      - action: "create_base"
        requirement:
          id: "base_001"
          title: "Base Requirement"
          description: "Initial requirement"
        expect_success: true
      - action: "attempt_duplicate"
        requirement:
          id: "dup_001"
          title: "Similar Requirement"
          description: "Similar to base"
        expect_warning: true
        expected_duplicate_ids: ["base_001"]
```

## Running Tests with Different Levels

```bash
# Run all tests (default)
pytest test_e2e_duplicate_detection.py

# Run only Level 1 tests (pure business rules)
TEST_LEVEL=1 pytest test_e2e_duplicate_detection.py

# Run Level 1 and 2 tests (no external dependencies)
TEST_LEVEL=2 pytest test_e2e_duplicate_detection.py

# Run all levels including E2E tests
TEST_LEVEL=3 pytest test_e2e_duplicate_detection.py
```

## Test Data Structure

The YAML file is organized by test levels:
- `test_level_1`: Pure business rule tests (no dependencies)
- `test_level_2`: Mock-based integration tests
- `test_level_3`: End-to-end tests with real system

Each level contains different types of test data:
- **similarity_cases**: Test similarity calculation between requirements
- **threshold_tests**: Test different threshold values
- **multiple_duplicates**: Test finding multiple duplicate candidates
- **integration_scenarios**: Test complete integration flows
- **search_scenarios**: Test search functionality
- **user_journeys**: Test realistic user workflows

## Fallback Behavior

If the YAML file is not found or fails to load, tests will:
1. Skip YAML-based tests with appropriate messages
2. Continue running inline test data (existing tests remain functional)
3. Log warnings about missing YAML data

This ensures tests remain robust even if the YAML file is missing or corrupted.

## Best Practices

1. **Keep test names descriptive**: Use clear, meaningful names for test cases
2. **Document expectations**: Add descriptions explaining what each test verifies
3. **Group related tests**: Organize similar test cases together
4. **Use realistic data**: Create test data that reflects real-world scenarios
5. **Maintain backward compatibility**: Don't remove or rename existing test cases without coordination

## Example: Adding a New Multi-Language Test

```yaml
test_level_1:
  similarity_cases:
    - name: "japanese_english_similarity"
      description: "Test similarity between Japanese and English requirements"
      req1:
        id: "jp_001"
        title: "認証機能"
        description: "ユーザーログイン処理"
      req2:
        id: "en_001"
        title: "Authentication Feature"
        description: "User login processing"
      min_similarity: 0.3  # Lower threshold for cross-language
      max_similarity: 0.7  # Not exact match due to language difference
      threshold: 0.5
```

This approach makes it easy to add comprehensive test coverage without modifying the test code itself.