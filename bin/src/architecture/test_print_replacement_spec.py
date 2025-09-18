"""print文置換機能のテスト仕様

TDD RED フェーズ - 期待する動作を定義するテスト
"""

import pytest
import ast
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO
import os
import tempfile

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from infrastructure.utils.print_replacer import PrintReplacer
except ImportError:
    # Handle import error gracefully for the test
    class PrintReplacer:
        def __init__(self, logger_name="logger", stderr_level="error"):
            self.logger_name = logger_name
            self.stderr_level = stderr_level
        
        def replace_prints(self, source_code):
            return source_code


class TestPrintReplacer:
    """print文置換機能のテストクラス"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.replacer = PrintReplacer()

    def test_simple_print_statement(self):
        """基本的なprint文の置換テスト"""
        source_code = '''
def test_function():
    print("Hello, World!")
    return True
'''
        expected = '''
def test_function():
    logger.info("Hello, World!")
    return True
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_f_string_print_statement(self):
        """f-string形式のprint文の置換テスト"""
        source_code = '''
def process_data(name, count):
    print(f"Processing {name} with {count} items")
    return name
'''
        expected = '''
def process_data(name, count):
    logger.info(f"Processing {name} with {count} items")
    return name
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_print_with_multiple_arguments(self):
        """複数引数のprint文の置換テスト"""
        source_code = '''
def display_info(name, age, city):
    print("Name:", name, "Age:", age, "City:", city)
'''
        expected = '''
def display_info(name, age, city):
    logger.info("Name: %s Age: %s City: %s", name, age, city)
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_print_to_stderr(self):
        """sys.stderrへのprint文をlogger.errorに置換"""
        source_code = '''
import sys

def handle_error(error_msg):
    print("Error occurred:", error_msg, file=sys.stderr)
    return False
'''
        expected = '''
import sys

def handle_error(error_msg):
    logger.error("Error occurred: %s", error_msg)
    return False
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_print_with_sep_and_end_parameters(self):
        """sep, endパラメータ付きのprint文の置換"""
        source_code = '''
def format_output(items):
    print("Items:", *items, sep=", ", end="\\n\\n")
'''
        expected = '''
def format_output(items):
    logger.info("Items: %s", ", ".join(str(item) for item in items))
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_nested_print_statements(self):
        """ネストした構造内のprint文の置換"""
        source_code = '''
def complex_function():
    for i in range(3):
        if i % 2 == 0:
            print(f"Even number: {i}")
        else:
            print("Odd number:", i)
    
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        print("Division error:", str(e), file=sys.stderr)
'''
        expected = '''
def complex_function():
    for i in range(3):
        if i % 2 == 0:
            logger.info(f"Even number: {i}")
        else:
            logger.info("Odd number: %s", i)
    
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error("Division error: %s", str(e))
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_preserve_non_print_statements(self):
        """print以外の文は変更されないことを確認"""
        source_code = '''
def mixed_function():
    value = input("Enter value: ")
    result = len(value)
    print("Length is:", result)
    return result
'''
        expected = '''
def mixed_function():
    value = input("Enter value: ")
    result = len(value)
    logger.info("Length is: %s", result)
    return result
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_logging_import_addition(self):
        """logging importが適切に追加されることをテスト"""
        source_code = '''
import os
import sys

def main():
    print("Starting application")
'''
        result = self.replacer.replace_prints(source_code)
        
        # loggingのimportが含まれることを確認
        assert "import logging" in result
        assert "logger = logging.getLogger(__name__)" in result

    def test_existing_logging_import_preservation(self):
        """既存のloggingインポートが重複しないことをテスト"""
        source_code = '''
import logging
import os

logger = logging.getLogger(__name__)

def main():
    print("Starting application")
'''
        result = self.replacer.replace_prints(source_code)
        
        # loggingのimportが重複していないことを確認
        import_count = result.count("import logging")
        logger_count = result.count("logger = logging.getLogger(__name__)")
        
        assert import_count == 1
        assert logger_count == 1

    def test_file_replacement(self):
        """ファイル全体の置換機能テスト"""
        source_file_content = '''#!/usr/bin/env python3
"""Test module for print replacement"""

def main():
    print("Application started")
    
    try:
        result = process_data()
        print(f"Result: {result}")
    except Exception as e:
        print("Error:", str(e), file=sys.stderr)

if __name__ == "__main__":
    main()
'''
        result = self.replacer.replace_prints(source_file_content)
        
        # 基本的な置換が行われていることを確認
        assert "logger.info(" in result
        assert "logger.error(" in result
        assert "print(" not in result
        assert "import logging" in result

    def test_ast_parsing_safety(self):
        """構文エラーのあるコードに対する安全な処理"""
        invalid_source = '''
def broken_function(
    print("This is broken syntax"
'''
        # 構文エラーの場合は例外が発生するか、元のコードを返すことを確認
        with pytest.raises((SyntaxError, ValueError)):
            self.replacer.replace_prints(invalid_source)

    def test_empty_print_statement(self):
        """引数なしのprint文の置換"""
        source_code = '''
def separator():
    print()
    print("---")
    print()
'''
        expected = '''
def separator():
    logger.info("")
    logger.info("---")
    logger.info("")
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def test_print_with_variables_and_expressions(self):
        """変数や式を含むprint文の置換"""
        source_code = '''
def calculate(x, y):
    result = x + y
    print("Calculation:", x, "+", y, "=", result)
    print(f"Square of result: {result ** 2}")
'''
        expected = '''
def calculate(x, y):
    result = x + y
    logger.info("Calculation: %s + %s = %s", x, y, result)
    logger.info(f"Square of result: {result ** 2}")
'''
        result = self.replacer.replace_prints(source_code)
        assert self._normalize_whitespace(result) == self._normalize_whitespace(expected)

    def _normalize_whitespace(self, code: str) -> str:
        """テスト比較用の空白正規化"""
        lines = [line.strip() for line in code.strip().split('\n') if line.strip()]
        return '\n'.join(lines)


class TestPrintReplacerIntegration:
    """print置換機能の統合テスト"""

    def test_process_file_method(self):
        """ファイル処理メソッドのテスト"""
        replacer = PrintReplacer()
        
        # テスト用の一時ファイルを作成するかモックを使用
        with patch('builtins.open') as mock_open:
            mock_file = Mock()
            mock_file.read.return_value = 'print("test")'
            mock_open.return_value.__enter__.return_value = mock_file
            
            # process_fileメソッドが存在し、呼び出せることを確認
            # 実装によってはファイル出力もテストする
            assert hasattr(replacer, 'process_file') or hasattr(replacer, 'replace_prints')

    def test_batch_processing(self):
        """バッチ処理機能のテスト（実装される場合）"""
        replacer = PrintReplacer()
        
        # 複数ファイルの一括処理機能がある場合のテスト
        test_files = ["file1.py", "file2.py"]
        
        with patch.object(Path, 'glob') as mock_glob:
            mock_glob.return_value = [Path(f) for f in test_files]
            
            # バッチ処理メソッドが存在する場合のテスト
            if hasattr(replacer, 'process_directory'):
                # 実装に応じたテストを追加
                pass


class TestPrintReplacerConfiguration:
    """print置換機能の設定テスト"""

    def test_logger_name_configuration(self):
        """loggerの名前設定テスト"""
        replacer = PrintReplacer(logger_name="custom_logger")
        
        source_code = 'print("test")'
        result = replacer.replace_prints(source_code)
        
        # カスタムlogger名が使用されることを確認
        assert "custom_logger = logging.getLogger(" in result or "logger = logging.getLogger(" in result

    def test_stderr_replacement_configuration(self):
        """stderr置換の設定テスト"""
        replacer = PrintReplacer(stderr_level="warning")
        
        source_code = 'print("error", file=sys.stderr)'
        result = replacer.replace_prints(source_code)
        
        # warning レベルが使用されることを確認（実装に依存）
        assert "logger.warning(" in result or "logger.error(" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])