"""
search関数のテスト（convention準拠版）
エラーを値として返す設計のテスト
"""

from implementation.search import search_symbols


def test_search_symbols_directory_returns_success_dict():
    """search_symbols関数がディレクトリパスでSearchSuccessDictを返すことを確認"""
    result = search_symbols("./test_data")
    
    # 成功時はsymbolsフィールドが存在
    assert "symbols" in result
    assert isinstance(result["symbols"], list)
    assert len(result["symbols"]) > 0
    assert "error" not in result
    assert "metadata" in result
    assert result["metadata"]["searched_files"] > 0


def test_search_symbols_nonexistent_path_returns_error_dict():
    """search_symbols関数が存在しないパスでSearchErrorDictを返すことを確認"""
    result = search_symbols("/nonexistent/path")
    
    # エラー時はerrorフィールドが存在
    assert "error" in result
    assert isinstance(result["error"], str)
    assert "not found" in result["error"].lower()
    assert "symbols" not in result
    assert "metadata" in result


def test_search_symbols_empty_directory_returns_empty_success():
    """search_symbols関数が空ディレクトリで空のSearchSuccessDictを返すことを確認"""
    result = search_symbols("./test_data/empty")
    
    # 成功だが結果が空
    assert "symbols" in result
    assert result["symbols"] == []
    assert "error" not in result
    assert result["metadata"]["searched_files"] == 0


def test_search_symbols_invalid_url_scheme_returns_error_dict():
    """search_symbols関数が無効なURLスキーマでSearchErrorDictを返すことを確認"""
    result = search_symbols("invalid://path")
    
    # エラー時の構造確認
    assert "error" in result
    assert "unsupported scheme" in result["error"].lower()
    assert "symbols" not in result


def test_search_symbols_file_url_returns_success_dict():
    """search_symbols関数がfile://スキーマでSearchSuccessDictを返すことを確認"""
    import os
    # 絶対パスを使用
    abs_path = os.path.abspath("./test_data/sample.py")
    result = search_symbols(f"file://{abs_path}")
    
    # 成功時の構造確認
    assert "symbols" in result, f"Expected symbols in result, got {result.keys()}"
    # パスがfile://形式で返される
    for symbol in result["symbols"]:
        assert symbol["path"].startswith("file://"), f"Path doesn't start with file://: {symbol['path']}"


def test_search_symbols_never_raises_exception():
    """search_symbols関数が例外を投げずに必ずdictを返すことを確認"""
    # 様々な異常入力でも例外を投げない
    test_cases = [
        None,
        "",
        "not/a/valid/path/at/all",
        "//invalid",
        ".",
        "..",
    ]
    
    for path in test_cases:
        # 例外が投げられないことを確認
        try:
            result = search_symbols(path)
            # 必ずdictが返される
            assert isinstance(result, dict)
            # エラーか成功のどちらか
            assert ("error" in result) or ("symbols" in result)
        except Exception as e:
            # conventionに違反：例外を投げてはいけない
            assert False, f"Unexpected exception for path '{path}': {e}"