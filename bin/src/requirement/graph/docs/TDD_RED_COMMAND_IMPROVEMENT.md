# /tdd_red コマンド改善提案

## 現状の問題点

TDD Redテストを作成した後、実際に失敗することを確認していなかった。

## 改善案：/tdd_red コマンドの手順

### 1. テストファイル作成段階
```bash
# 失敗するテストを作成
/tdd_red <feature_name>
```

### 2. 【新規追加】Red確認段階
```bash
# 必須: テストが失敗することを確認
./test.sh | grep -E "(FAILED|ERROR)" | grep <test_file_name>

# 失敗が確認できない場合は修正が必要
```

### 3. 【新規追加】失敗パターン分析段階
```bash
# 期待される失敗パターンを確認
# - NotImplementedError: 未実装機能のテスト ✓
# - ImportError: まだ存在しないモジュール ✓
# - AssertionError: 期待値と異なる動作 ✓
# - その他のエラー: 要確認
```

### 4. 【新規追加】ドキュメント化段階
```markdown
## TDD Red 確認結果

- テストファイル: test_<feature_name>.py
- 失敗テスト数: X件
- 失敗理由: NotImplementedError（未実装）
- 実装場所: application/<module_name>.py
```

## 改善されたコマンドフロー

```python
def tdd_red_command(feature_name):
    # 1. テストファイル作成
    create_failing_test(feature_name)
    
    # 2. Red確認（新規）
    result = run_test_and_verify_failure()
    if not result.has_failures:
        raise Error("TDD Red失敗: テストが通ってしまっています")
    
    # 3. 失敗パターン確認（新規）
    analyze_failure_patterns(result)
    
    # 4. レポート生成（新規）
    generate_tdd_red_report(feature_name, result)
    
    return "TDD Red完了: テストの失敗を確認しました"
```

## 今回の実例

### 1. テストファイル作成
`test_inconsistency_detection.py` を作成

### 2. Red確認実行
```bash
./test.sh
```

### 3. 失敗確認結果
```
FAILED test_inconsistency_detection.py::TestSemanticConflictDetection::test_detect_conflicting_performance_requirements
FAILED test_inconsistency_detection.py::TestSemanticConflictDetection::test_detect_contradictory_security_policies
FAILED test_inconsistency_detection.py::TestResourceConflictDetection::test_detect_database_connection_pool_conflict
FAILED test_inconsistency_detection.py::TestPriorityConsistencyChecking::test_detect_priority_dependency_inversion
FAILED test_inconsistency_detection.py::TestRequirementCompleteness::test_detect_missing_security_requirements
FAILED test_inconsistency_detection.py::TestRequirementCompleteness::test_detect_duplicate_requirements
```

すべて`NotImplementedError`で失敗 ✓

### 4. 実装必要モジュール
- `application/semantic_validator.py`
- `application/resource_conflict_detector.py`
- `application/priority_consistency_checker.py`
- `application/requirement_completeness_analyzer.py`
- `application/integrated_consistency_validator.py`

## チェックリスト

- [ ] テストファイルが作成されている
- [x] `./test.sh`でテストが失敗する
- [x] 失敗理由が`NotImplementedError`である
- [x] 実装すべきモジュールが明確である
- [x] ドキュメントが作成されている

## まとめ

/tdd_red コマンドは以下を保証すべき：
1. 失敗するテストを作成する
2. **実際に失敗することを確認する**（新規）
3. 失敗パターンが適切である
4. 実装への道筋が明確である