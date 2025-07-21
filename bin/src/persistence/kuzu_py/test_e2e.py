"""
End-to-end tests for kuzu_py package

外部インポート可能性とflake inputとしての利用を検証
"""

import subprocess
import tempfile
import os
import sys
from pathlib import Path


def test_external_import():
    """パッケージが外部から正しくインポートできることを確認"""
    # ソースディレクトリ外で実行
    with tempfile.TemporaryDirectory() as tmpdir:
        test_script = Path(tmpdir) / "test_import.py"
        test_script.write_text("""
import kuzu_py
from kuzu_py import create_database, create_connection
from kuzu_py import DatabaseResult, ConnectionResult, ErrorDict

# KuzuDB APIが露出していることを確認
assert hasattr(kuzu_py, 'Database')
assert hasattr(kuzu_py, 'Connection')

# ヘルパー関数が利用可能なことを確認
db = create_database()
assert db is not None

print("✓ External import successful")
""")
        
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "✓ External import successful" in result.stdout


def test_package_location():
    """パッケージがsite-packagesにインストールされていることを確認"""
    result = subprocess.run(
        [sys.executable, "-c", "import kuzu_py; print(kuzu_py.__file__)"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "site-packages" in result.stdout or "/nix/store" in result.stdout
    assert "/home/nixos/bin/src/persistence/kuzu_py" not in result.stdout


def test_no_pythonpath_dependency():
    """PYTHONPATH設定なしで動作することを確認"""
    # 環境変数からPYTHONPATHを削除
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    
    result = subprocess.run(
        [sys.executable, "-c", "import kuzu_py; print('OK')"],
        capture_output=True,
        text=True,
        env=env
    )
    
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_flake_input_simulation():
    """他プロジェクトからflake inputとして利用できることをシミュレート"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 擬似的な外部プロジェクト
        test_project = Path(tmpdir) / "test_app.py"
        test_project.write_text("""
from kuzu_py import create_database, create_connection

# In-memory DBを作成
db_result = create_database()
if hasattr(db_result, 'ok') and not db_result['ok']:
    raise Exception(f"DB creation failed: {db_result}")

# 接続を作成
conn_result = create_connection(db_result)
if hasattr(conn_result, 'ok') and not conn_result['ok']:
    raise Exception(f"Connection failed: {conn_result}")

# 基本的なクエリを実行
conn_result.execute("CREATE NODE TABLE person(name STRING, age INT64, PRIMARY KEY(name))")
conn_result.execute("CREATE (p:person {name: 'Alice', age: 30})")

result = conn_result.execute("MATCH (p:person) RETURN p.name, p.age")
data = [(row[0], row[1]) for row in result]
assert data == [('Alice', 30)]

print("✓ Flake input simulation successful")
""")
        
        result = subprocess.run(
            [sys.executable, str(test_project)],
            capture_output=True,
            text=True,
            cwd=tmpdir  # ソースディレクトリ外で実行
        )
        
        assert result.returncode == 0, f"Execution failed: {result.stderr}"
        assert "✓ Flake input simulation successful" in result.stdout


def test_all_exports_available():
    """__all__で定義された全エクスポートが利用可能なことを確認"""
    test_code = """
import kuzu_py

# __all__の内容を確認
expected_exports = [
    "create_database",
    "create_connection", 
    "DatabaseResult",
    "ConnectionResult",
    "ErrorDict",
]

for export in expected_exports:
    assert hasattr(kuzu_py, export), f"{export} not found in kuzu_py"
    
print("✓ All exports available")
"""
    
    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Export check failed: {result.stderr}"
    assert "✓ All exports available" in result.stdout


if __name__ == "__main__":
    # 各テストを実行
    print("Running e2e tests...")
    
    test_external_import()
    print("✓ test_external_import")
    
    test_package_location()
    print("✓ test_package_location")
    
    test_no_pythonpath_dependency()
    print("✓ test_no_pythonpath_dependency")
    
    test_flake_input_simulation()
    print("✓ test_flake_input_simulation")
    
    test_all_exports_available()
    print("✓ test_all_exports_available")
    
    print("\nAll e2e tests passed! 🎉")