"""ユニットテスト - 個別関数のテスト
Run with: nix develop -c uv run pytest test_unit.py
"""

import pytest
import os
from main import (
    _is_hidden, _is_empty_dir, _get_file_count, _get_subdirs,
    _extract_flake_description, _extract_package_json_description,
    _extract_python_docstring, _get_readme_content
)


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""
    
    def test_is_hidden_ドット始まり_True返却(self):
        """ドットで始まるパスは隠しファイル判定"""
        assert _is_hidden(".git") is True
        assert _is_hidden("/path/to/.hidden") is True
    
    def test_is_hidden_通常パス_False返却(self):
        """通常のパスは隠しファイルではない"""
        assert _is_hidden("normal") is False
        assert _is_hidden("/path/to/visible") is False
    
    def test_is_empty_dir_空ディレクトリ_True返却(self, temp_dir):
        """空ディレクトリの判定"""
        empty_dir = f"{temp_dir}/empty"
        os.makedirs(empty_dir)
        assert _is_empty_dir(empty_dir) is True
    
    def test_is_empty_dir_ファイルあり_False返却(self, temp_dir):
        """ファイルがあるディレクトリは空ではない"""
        dir_with_file = f"{temp_dir}/with_file"
        os.makedirs(dir_with_file)
        open(f"{dir_with_file}/test.txt", 'w').close()
        assert _is_empty_dir(dir_with_file) is False
    
    def test_get_file_count_正確なカウント_ファイル数返却(self, temp_dir):
        """ディレクトリ内のファイル数を正確にカウント"""
        test_dir = f"{temp_dir}/test"
        os.makedirs(test_dir)
        
        # ファイル作成
        for i in range(3):
            open(f"{test_dir}/file{i}.txt", 'w').close()
        
        # サブディレクトリ（カウントされない）
        os.makedirs(f"{test_dir}/subdir")
        
        assert _get_file_count(test_dir) == 3
    
    def test_get_subdirs_サブディレクトリ名_リスト返却(self, temp_dir):
        """直下のサブディレクトリ名のリストを返却"""
        test_dir = f"{temp_dir}/test"
        os.makedirs(test_dir)
        
        # サブディレクトリ作成
        subdirs = ['sub1', 'sub2', '.hidden']
        for subdir in subdirs:
            os.makedirs(f"{test_dir}/{subdir}")
        
        # ファイル（含まれない）
        open(f"{test_dir}/file.txt", 'w').close()
        
        result = _get_subdirs(test_dir)
        assert set(result) == set(subdirs)


class TestMetadataExtraction:
    """メタデータ抽出関数のテスト"""
    
    def test_extract_flake_description_正常_説明文返却(self, temp_dir):
        """flake.nixからdescriptionを抽出"""
        with open(f"{temp_dir}/flake.nix", 'w') as f:
            f.write('{\n  description = "Test POC for search";\n}')
        
        result = _extract_flake_description(temp_dir)
        assert result == "Test POC for search"
    
    def test_extract_flake_description_ファイルなし_None返却(self, temp_dir):
        """flake.nixがない場合はNone"""
        result = _extract_flake_description(temp_dir)
        assert result is None
    
    def test_extract_package_json_description_正常_説明文返却(self, temp_dir):
        """package.jsonからdescriptionを抽出"""
        with open(f"{temp_dir}/package.json", 'w') as f:
            f.write('{"name": "test", "description": "Test package"}')
        
        result = _extract_package_json_description(temp_dir)
        assert result == "Test package"
    
    def test_extract_python_docstring_正常_docstring返却(self, temp_dir):
        """Pythonファイルからdocstringを抽出"""
        with open(f"{temp_dir}/main.py", 'w') as f:
            f.write('"""This is a test module"""\n\nimport os\n')
        
        result = _extract_python_docstring(temp_dir)
        assert result == "This is a test module"
    
    def test_get_readme_content_存在する場合_内容返却(self, temp_dir):
        """READMEファイルの内容を取得"""
        content = "# Test README\n\nThis is a test."
        with open(f"{temp_dir}/README.md", 'w') as f:
            f.write(content)
        
        result = _get_readme_content(temp_dir)
        assert result == content
    
    def test_get_readme_content_大文字小文字_対応(self, temp_dir):
        """README.md, readme.md, Readme.md に対応"""
        variants = ['readme.md', 'Readme.md']
        
        for variant in variants:
            # 前のファイルを削除
            for v in ['README.md', 'readme.md', 'Readme.md']:
                path = f"{temp_dir}/{v}"
                if os.path.exists(path):
                    os.remove(path)
            
            # テストファイル作成
            with open(f"{temp_dir}/{variant}", 'w') as f:
                f.write(f"Content from {variant}")
            
            result = _get_readme_content(temp_dir)
            assert result == f"Content from {variant}"


class TestEnvironmentVariables:
    """環境変数関連のテスト"""
    
    def test_環境変数取得_必須変数_エラー時例外(self):
        """必須環境変数が未設定の場合は例外"""
        from infrastructure.variables.env import get_scan_root_path
        
        # 環境変数を一時的に削除
        old_value = os.environ.pop('DIRSCAN_ROOT_PATH', None)
        
        try:
            with pytest.raises(RuntimeError):
                get_scan_root_path()
        finally:
            # 復元
            if old_value:
                os.environ['DIRSCAN_ROOT_PATH'] = old_value
    
    def test_環境変数取得_オプション変数_None返却(self):
        """オプション環境変数が未設定の場合はNone"""
        from infrastructure.variables.env import get_exclude_patterns
        
        # 環境変数を一時的に削除
        old_value = os.environ.pop('DIRSCAN_EXCLUDE_PATTERNS', None)
        
        try:
            result = get_exclude_patterns()
            assert result is None
        finally:
            # 復元
            if old_value:
                os.environ['DIRSCAN_EXCLUDE_PATTERNS'] = old_value