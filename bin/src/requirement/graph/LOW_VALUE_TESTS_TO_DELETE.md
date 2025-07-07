# Low-Value Tests to Delete in infrastructure/

Based on the testing conventions that favor behavior testing over implementation testing, the following tests should be deleted:

## test_database_factory.py

### Tests to Delete:
1. **test_singleton_pattern** (lines 53-82)
   - Tests implementation detail (singleton pattern)
   - Not testing behavior, just internal caching mechanism
   - Already skipped in test mode

2. **test_import_error_handling** (lines 78-82)
   - Already marked as skip
   - Tests implementation detail of import error handling
   - Not testing actual behavior

## test_custom_procedures.py

### Tests to Delete:
None - All tests verify actual behavior of procedures, not implementation details.

## test_cypher_executor.py

### Tests to Delete:
1. **test_execute_empty_query_returns_error** (lines 182-213)
   - Tests implementation detail (empty query handling)
   - Should be handled by query validator, not executor

## test_ddl_schema_manager.py

### Tests to Delete:
1. **test_parse_cypher_statements_コメント除去_正しくパース** (lines 16-41)
   - Tests internal parsing implementation
   - Private method testing
   
2. **test_generate_drop_statement_各種CREATE_DROP生成** (lines 42-59)
   - Tests internal implementation detail
   - Private method testing

3. **test_handle_duplicate_rel_tables_重複テーブル_リネーム** (lines 60-81)
   - Tests internal implementation detail
   - Private method testing

## test_graph_validators.py

### Tests to Delete:
None - All tests verify actual validation behavior, not implementation details.

## test_jsonl_repository.py

### Tests to Delete:
None - Tests verify actual CRUD behavior through the repository interface.

## test_kuzu_repository.py

### Tests to Delete:
1. **setup_method** (lines 102-106)
   - Just sets environment variable, not a real test
   - Should be handled by fixture or test environment setup

## test_main_udf_integration.py

### Tests to Delete:
1. **test_main_環境変数制御_動的URI生成** (lines 58-77)
   - Tests environment variable behavior
   - Implementation detail of how URIs are generated

2. **test_UDF登録がmain起動時に実行される** (lines 155-174)
   - Tests implementation detail of UDF registration
   - Should test behavior, not registration mechanics

## test_query_validator.py

### Tests to Delete:
1. **test_sanitize_parameters_removes_dangerous_values** (lines 79-94)
   - Tests implementation detail of sanitization
   - Should focus on query validation behavior

2. **test_sanitize_parameters_handles_non_string_values** (lines 156-173)
   - Tests implementation detail of parameter handling
   - Low value, focuses on HOW not WHAT

## test_requirement_validator.py

### Tests to Delete:
None - All tests verify actual validation behavior with specific business rules.

## test_unified_query_interface.py

### Tests to Delete:
1. **test_parse_procedure_args_handles_types** (lines 87-101)
   - Tests internal parsing implementation
   - Private method testing

2. **test_detect_query_type_correctly_identifies** (lines 112-122)
   - Tests internal classification logic
   - Private method testing

3. **test_empty_procedure_args_parsed_correctly** (lines 158-162)
   - Tests edge case of internal parsing
   - Private method testing

4. **test_split_mixed_query_handles_complex_queries** (lines 164-177)
   - Tests internal query splitting logic
   - Private method testing

## test_apply_ddl_schema.py

### Tests to Delete:
None - Tests actual schema application behavior.

## variables/test_env.py

This is not a test file but a test utility module - no tests to delete.

## Summary

Total tests to delete: **14 tests**

These tests focus on implementation details (HOW) rather than behavior (WHAT), test private methods, or check internal mechanics rather than observable behavior. Deleting these will improve the test suite by focusing on valuable behavior tests.