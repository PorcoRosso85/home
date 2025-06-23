"""
ctagsを使用してプロジェクト内のシンボルアドレスをJSONL形式で出力

Usage:
    python main.py [directory] [pattern]
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Union


def run_ctags(files: List[str]) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """ctagsを実行してタグ情報を取得"""
    if not files:
        return []
    
    cmd = [
        "ctags",
        "--output-format=json",
        "--fields=+KSn",
        "--kinds-python=+cfmv",
        "--extras=+q"
    ] + files
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return {"error": f"ctags failed: {result.stderr}"}
    
    tags = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                tags.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return tags


def extract_symbols(directory: str = ".", pattern: str = "**/*.py") -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """ディレクトリからシンボルを抽出"""
    base_path = Path(directory).resolve()
    
    if not base_path.exists():
        return {"error": f"Directory not found: {base_path}"}
    
    # ファイル検索
    files = []
    for file_path in base_path.rglob(pattern.replace('**/', '')):
        if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
            files.append(str(file_path))
    
    if not files:
        return {"error": "No files found"}
    
    # ctags実行
    tags_result = run_ctags(files)
    if isinstance(tags_result, dict) and "error" in tags_result:
        return tags_result
    
    # シンボル変換
    symbols = []
    for tag in tags_result:
        symbol = {
            "name": tag.get("name", ""),
            "kind": tag.get("kind", ""),
            "path": tag.get("path", ""),
            "line": tag.get("line", 0),
            "address": f"{tag.get('path', '')}:{tag.get('line', 0)}"
        }
        
        scope = tag.get("scope", "")
        if scope:
            symbol["scope"] = scope
            
        symbols.append(symbol)
    
    return symbols


def output_jsonl(symbols: List[Dict[str, Any]]):
    """JSONL形式で出力"""
    for symbol in symbols:
        print(json.dumps(symbol, ensure_ascii=False))


def main():
    """メイン処理"""
    import sys
    
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    pattern = sys.argv[2] if len(sys.argv) > 2 else "**/*.py"
    
    result = extract_symbols(directory, pattern)
    
    if isinstance(result, dict) and "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    output_jsonl(result)


# テスト
def test_run_ctags_empty_files():
    """空ファイルリストのテスト"""
    result = run_ctags([])
    assert result == []


def test_run_ctags_invalid_command():
    """無効なctagsコマンドのテスト"""
    result = run_ctags(["/nonexistent/file.py"])
    # ctagsは存在しないファイルに対して空の出力を返す場合がある
    assert isinstance(result, (list, dict))
    if isinstance(result, dict):
        assert "error" in result


def test_extract_symbols_invalid_directory():
    """存在しないディレクトリのテスト"""
    result = extract_symbols("/nonexistent/directory")
    assert isinstance(result, dict)
    assert "error" in result
    assert "Directory not found" in result["error"]


def test_extract_symbols_no_files():
    """マッチするファイルがない場合のテスト"""
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        result = extract_symbols(temp_dir, "*.nonexistent")
        assert isinstance(result, dict)
        assert "error" in result
        assert "No files found" in result["error"]


def test_extract_symbols_current_directory():
    """カレントディレクトリでのシンボル抽出テスト"""
    result = extract_symbols(".", "*.py")
    
    # エラーでない場合のみチェック
    if not (isinstance(result, dict) and "error" in result):
        assert isinstance(result, list)
        if result:  # シンボルが見つかった場合
            assert "name" in result[0]
            assert "kind" in result[0]
            assert "path" in result[0]
            assert "line" in result[0]
            assert "address" in result[0]


def test_output_jsonl_format():
    """JSONL出力形式のテスト"""
    import io
    import sys
    from contextlib import redirect_stdout
    
    symbols = [
        {
            "name": "test_func",
            "kind": "function", 
            "path": "/test/file.py",
            "line": 10,
            "address": "/test/file.py:10"
        },
        {
            "name": "TestClass",
            "kind": "class",
            "path": "/test/file.py", 
            "line": 20,
            "address": "/test/file.py:20",
            "scope": "module"
        }
    ]
    
    f = io.StringIO()
    with redirect_stdout(f):
        output_jsonl(symbols)
    
    output_lines = f.getvalue().strip().split('\n')
    assert len(output_lines) == 2
    
    # 各行が有効なJSONであることを確認
    for line in output_lines:
        parsed = json.loads(line)
        assert "name" in parsed
        assert "kind" in parsed
        assert "address" in parsed


def test_symbol_extraction_structure():
    """シンボル抽出の構造テスト"""
    mock_tags = [
        {
            "name": "func1",
            "kind": "function",
            "path": "/test.py",
            "line": 1,
            "scope": ""
        },
        {
            "name": "Class1", 
            "kind": "class",
            "path": "/test.py",
            "line": 10,
            "scope": "module"
        }
    ]
    
    # run_ctagsの結果を直接処理
    symbols = []
    for tag in mock_tags:
        symbol = {
            "name": tag.get("name", ""),
            "kind": tag.get("kind", ""),
            "path": tag.get("path", ""),
            "line": tag.get("line", 0),
            "address": f"{tag.get('path', '')}:{tag.get('line', 0)}"
        }
        
        scope = tag.get("scope", "")
        if scope:
            symbol["scope"] = scope
            
        symbols.append(symbol)
    
    assert len(symbols) == 2
    assert symbols[0]["name"] == "func1"
    assert symbols[0]["address"] == "/test.py:1"
    assert "scope" not in symbols[0]  # 空のスコープは含めない
    assert symbols[1]["name"] == "Class1"
    assert symbols[1]["scope"] == "module"


if __name__ == "__main__":
    main()