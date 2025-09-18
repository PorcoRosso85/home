#!/usr/bin/env python3
"""
ドメイン層：検証ロジックの仕様

このテストは、Pythonツールの出力を解析・検証するビジネスロジックの
振る舞いを定義します。各ツールの出力形式（JSON/テキスト）に対応し、
問題の重要度別に分類して構造化された分析結果を提供します。
"""

import pytest
import json
import sys
import os

# テストからモジュールをインポートできるようにパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.validation import (
    validate_pyright_output,
    validate_pytest_output,
    validate_ruff_output,
)


class TestPyrightOutputValidation:
    """Pyright（型チェッカー）の出力検証仕様"""
    
    def test_json形式の型エラーを構造化された分析結果に変換する(self):
        """仕様：JSON形式の診断情報から、重要度別に分類された問題リストを生成する"""
        pyright_json = {
            "diagnostics": [
                {
                    "severity": "error",
                    "message": "Type error",
                    "file": {"uri": "test.py"},
                    "range": {
                        "start": {"line": 10, "character": 5},
                        "end": {"line": 10, "character": 10}
                    }
                }
            ]
        }
        
        result = validate_pyright_output(json.dumps(pyright_json))
        
        # 型エラーが存在する場合、validはFalseになる
        assert result['valid'] is False
        # 1つの型エラーが問題として抽出される
        assert len(result['issues']) == 1
        assert result['issues'][0]['severity'] == 'error'
        # サマリーにエラー数が集計される
        assert result['summary']['error_count'] == 1


    def test_テキスト形式の診断メッセージをパースして分析結果を生成する(self):
        """仕様：pyrightのCLI出力（行番号:列番号形式）から構造化データを抽出する"""
        output = """
        test.py:10:5 - error: Variable not defined
        test.py:20:10 - warning: Unused variable
        """
        
        result = validate_pyright_output(output)
        
        # エラーまたは警告が存在する場合、validはFalseになる
        assert result['valid'] is False
        # 2つの問題（1エラー、1警告）が正しく分類される
        assert len(result['issues']) == 2
        assert result['summary']['error_count'] == 1
        assert result['summary']['warning_count'] == 1


class TestPytestOutputValidation:
    """Pytest（テストランナー）の出力検証仕様"""
    
    def test_json_reportプラグインの出力からテスト結果サマリーを生成する(self):
        """仕様：pytest-json-reportの出力から、テストの成功/失敗状況を分析する"""
        pytest_json = {
            "summary": {
                "passed": 5,
                "failed": 2,
                "skipped": 1,
                "error": 0
            },
            "tests": [
                {
                    "outcome": "failed",
                    "nodeid": "test_example.py::test_something",
                    "call": {
                        "longrepr": "AssertionError: assert False"
                    }
                }
            ]
        }
        
        result = validate_pytest_output("", json.dumps(pytest_json))
        
        # 失敗したテストが存在する場合、validはFalseになる
        assert result['valid'] is False
        # 失敗したテストが問題として記録される
        assert len(result['issues']) == 1
        # テスト結果の統計が正確に集計される
        assert result['summary']['failed'] == 2
        assert result['summary']['passed'] == 5


class TestRuffOutputValidation:
    """Ruff（リンター）の出力検証仕様"""
    
    def test_リンティング違反を構造化された問題リストに変換する(self):
        """仕様：ruffの違反レポートから、ファイル・行・列・ルールコードを抽出する"""
        output = """test.py:10:5: F401 'os' imported but unused
test.py:20:1: E302 expected 2 blank lines, found 1"""
        
        result = validate_ruff_output(output)
        
        # リンティング違反が存在する場合、validはFalseになる
        assert result['valid'] is False
        # 2つのリンティング違反が検出される
        assert len(result['issues']) == 2
        # 各違反の位置情報が正確に抽出される
        assert result['issues'][0]['file'] == 'test.py'
        assert result['issues'][0]['line'] == 10
        assert result['issues'][0]['column'] == 5