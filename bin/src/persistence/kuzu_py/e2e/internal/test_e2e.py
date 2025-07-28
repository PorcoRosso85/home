"""
End-to-end tests for kuzu_py package

外部インポート可能性とflake inputとしての利用を検証
"""

import subprocess
import tempfile
import os
import sys
from pathlib import Path


class TestExternalImport:
    """外部インポート関連のテスト"""
    
    def run_python_code(self, code: str, env=None, cwd=None):
        """Pythonコードを実行するヘルパー関数"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd
        )
        return result
    
    def run_python_script(self, script_path: Path, env=None, cwd=None):
        """Pythonスクリプトを実行するヘルパー関数"""
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd
        )
        return result
    
    def test_basic_import(self):
        """基本的なインポートテスト"""
        result = self.run_python_code("import kuzu_py; print('OK')")
        assert result.returncode == 0
        assert "OK" in result.stdout
    
    def test_exports_available(self):
        """エクスポートされた関数・型の確認"""
        code = """
import kuzu_py

# エクスポートされているべき項目
exports = ["create_database", "create_connection", 
           "DatabaseResult", "ConnectionResult", "ErrorDict"]

for item in exports:
    assert hasattr(kuzu_py, item), f"{item} not found"
    
# KuzuDB APIの露出確認
assert hasattr(kuzu_py, 'Database')
assert hasattr(kuzu_py, 'Connection')

print("✓ All exports available")
"""
        result = self.run_python_code(code)
        assert result.returncode == 0
        assert "✓ All exports available" in result.stdout
    
    def test_package_location(self):
        """パッケージの場所確認（開発環境では開発ディレクトリも許容）"""
        result = self.run_python_code("import kuzu_py; print(kuzu_py.__file__)")
        assert result.returncode == 0
        # 開発環境、パッケージ環境、Nixストアのいずれかから読み込まれることを確認
        valid_locations = [
            "site-packages",
            "/nix/store", 
            "/home/nixos/bin/src/persistence/kuzu_py"
        ]
        assert any(loc in result.stdout for loc in valid_locations)
    
    def test_no_pythonpath_dependency(self):
        """PYTHONPATH依存なしで動作することを確認"""
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        
        result = self.run_python_code("import kuzu_py; print('OK')", env=env)
        assert result.returncode == 0
        assert "OK" in result.stdout
    
    def test_external_project_usage(self):
        """外部プロジェクトからの利用シミュレーション"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_script = Path(tmpdir) / "test_app.py"
            test_script.write_text("""
from kuzu_py import create_database, create_connection

# 基本的な使用例
db = create_database()  # in-memory DB
assert db is not None

conn = create_connection(db)
assert conn is not None

# KuzuDBの基本操作
conn.execute("CREATE NODE TABLE test(id INT64, PRIMARY KEY(id))")
conn.execute("CREATE (:test {id: 1})")
result = conn.execute("MATCH (t:test) RETURN t.id")
assert result.get_next()[0] == 1

print("✓ External usage successful")
""")
            
            result = self.run_python_script(test_script, cwd=tmpdir)
            assert result.returncode == 0, f"Failed: {result.stderr}"
            assert "✓ External usage successful" in result.stdout


# pytest用のテスト関数
def test_basic_import():
    """基本的なインポートテスト"""
    t = TestExternalImport()
    t.test_basic_import()


def test_exports_available():
    """エクスポートされた関数・型の確認"""
    t = TestExternalImport()
    t.test_exports_available()


def test_package_location():
    """パッケージの場所確認"""
    t = TestExternalImport()
    t.test_package_location()


def test_no_pythonpath_dependency():
    """PYTHONPATH非依存の確認"""
    t = TestExternalImport()
    t.test_no_pythonpath_dependency()


def test_external_project_usage():
    """外部プロジェクトからの利用"""
    t = TestExternalImport()
    t.test_external_project_usage()


if __name__ == "__main__":
    # 直接実行時の簡易テストランナー
    t = TestExternalImport()
    tests = [
        ("Basic import", t.test_basic_import),
        ("Exports available", t.test_exports_available),
        ("Package location", t.test_package_location),
        ("No PYTHONPATH dependency", t.test_no_pythonpath_dependency),
        ("External project usage", t.test_external_project_usage),
    ]
    
    print("Running e2e tests...")
    failed_tests = []
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed_tests.append((name, str(e)))
    
    if failed_tests:
        print(f"\n{len(failed_tests)} test(s) failed:")
        for name, error in failed_tests:
            print(f"  - {name}: {error}")
        import sys
        sys.exit(1)
    else:
        print("\nAll e2e tests passed! 🎉")