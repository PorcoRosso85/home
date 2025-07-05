"""
TDD Red Phase - Symbol Search Tests
統一された出力形式でシンボル探索を行うテスト
"""

import pytest
from pathlib import Path
from typing import Dict, Any
from search import SearchResult, Symbol, search_symbols


class TestSearchSymbols:
    """シンボル探索のテスト"""
    
    def test_search_result_structure(self):
        """SearchResult型の構造を確認"""
        # ディレクトリを指定して検索
        result = search_symbols("./test_data")
        
        # 必須フィールドの存在確認
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "metadata" in result
        
        # 型の確認
        assert isinstance(result["success"], bool)
        assert result["data"] is None or isinstance(result["data"], list)
        assert result["error"] is None or isinstance(result["error"], str)
        assert isinstance(result["metadata"], dict)
    
    def test_symbol_structure(self):
        """Symbol型の構造を確認"""
        result = search_symbols("./test_data/sample.py")
        
        assert result["success"] is True
        assert result["data"] is not None
        assert len(result["data"]) > 0
        
        symbol = result["data"][0]
        
        # 必須フィールド
        assert "name" in symbol
        assert "type" in symbol
        assert "path" in symbol
        assert "line" in symbol
        
        # 型の確認
        assert isinstance(symbol["name"], str)
        assert symbol["type"] in ["function", "class", "method", "variable", 
                                 "constant", "import", "type_alias"]
        assert isinstance(symbol["path"], str)
        assert isinstance(symbol["line"], int)
    
    def test_directory_search(self):
        """ディレクトリ配下のシンボル探索"""
        result = search_symbols("./test_data")
        
        assert result["success"] is True
        assert result["data"] is not None
        assert len(result["data"]) >= 5  # 複数のシンボルが見つかること
        
        # メタデータの確認
        assert "searched_files" in result["metadata"]
        assert "search_time_ms" in result["metadata"]
        assert result["metadata"]["searched_files"] > 0
    
    def test_file_url_scheme(self):
        """file://スキーマでの探索"""
        result = search_symbols("file://./test_data/sample.py")
        
        assert result["success"] is True
        assert result["data"] is not None
        
        # パスがfile://形式で返される
        for symbol in result["data"]:
            assert symbol["path"].startswith("file://")
    
    def test_python_symbols(self):
        """Pythonファイルの各種シンボル検出"""
        result = search_symbols("./test_data/sample.py")
        
        assert result["success"] is True
        symbols = result["data"]
        
        # 各種シンボルタイプが検出されること
        symbol_types = {s["type"] for s in symbols}
        assert "function" in symbol_types
        assert "class" in symbol_types
        assert "variable" in symbol_types
    
    def test_error_handling_nonexistent_path(self):
        """存在しないパスのエラーハンドリング"""
        result = search_symbols("/nonexistent/path")
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] is not None
        assert "not found" in result["error"].lower()
    
    def test_error_handling_invalid_url(self):
        """無効なURLスキーマのエラーハンドリング"""
        result = search_symbols("invalid://path")
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] is not None
        assert "unsupported scheme" in result["error"].lower()
    
    def test_empty_directory(self):
        """空のディレクトリの処理"""
        result = search_symbols("./test_data/empty")
        
        assert result["success"] is True
        assert result["data"] == []
        assert result["error"] is None
        assert result["metadata"]["searched_files"] == 0
    
    def test_mixed_file_types(self):
        """複数の言語ファイルが混在する場合"""
        result = search_symbols("./test_data/mixed")
        
        assert result["success"] is True
        assert result["data"] is not None
        
        # 異なる拡張子のファイルからシンボルを検出
        paths = {s["path"] for s in result["data"]}
        extensions = {Path(p).suffix for p in paths}
        assert len(extensions) >= 2  # 複数の拡張子


class TestSymbolDetails:
    """シンボルの詳細情報テスト"""
    
    def test_function_symbol(self):
        """関数シンボルの詳細"""
        result = search_symbols("./test_data/functions.py")
        functions = [s for s in result["data"] if s["type"] == "function"]
        
        assert len(functions) > 0
        func = functions[0]
        
        assert func["name"] != ""
        assert func["line"] > 0
        assert "column" in func  # オプショナル
        assert "context" in func  # オプショナル、関数シグネチャなど
    
    def test_class_symbol(self):
        """クラスシンボルの詳細"""
        result = search_symbols("./test_data/classes.py")
        classes = [s for s in result["data"] if s["type"] == "class"]
        
        assert len(classes) > 0
        cls = classes[0]
        
        assert cls["name"] != ""
        assert cls["line"] > 0
        
        # クラス内のメソッドも検出されること
        methods = [s for s in result["data"] 
                  if s["type"] == "method" and s["line"] > cls["line"]]
        assert len(methods) > 0
    
    def test_symbol_context(self):
        """シンボルのコンテキスト情報"""
        result = search_symbols("./test_data/sample.py")
        
        for symbol in result["data"]:
            if "context" in symbol:
                assert isinstance(symbol["context"], str)
                assert len(symbol["context"]) > 0
                assert len(symbol["context"]) <= 200  # 適切な長さ


if __name__ == "__main__":
    pytest.main([__file__, "-v"])