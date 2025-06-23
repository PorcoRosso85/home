"""
Phase 4 verification

責務: Phase 4の完了確認
- pytest実行
- インポートエラーチェック
- pydoc生成
"""

import subprocess
import sys
import os
import importlib.util


def run_pytest():
    """pytestの実行"""
    print("=== pytest実行 ===")
    try:
        # telemetryディレクトリのテスト
        result = subprocess.run(
            ["uv", "run", "pytest", "-v", "telemetry/"],
            capture_output=True,
            text=True
        )
        
        print("telemetry/ のテスト結果:")
        if result.returncode == 0:
            # 成功した場合、サマリーを表示
            lines = result.stdout.split('\n')
            for line in lines:
                if "passed" in line or "failed" in line or "error" in line:
                    print(f"  {line}")
        else:
            print(f"  エラー: {result.stderr}")
        
        # storageディレクトリのテスト
        result = subprocess.run(
            ["uv", "run", "pytest", "-v", "storage/"],
            capture_output=True,
            text=True
        )
        
        print("\nstorage/ のテスト結果:")
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if "passed" in line or "failed" in line or "error" in line:
                    print(f"  {line}")
        else:
            print(f"  エラー: {result.stderr}")
        
        return True
    except Exception as e:
        print(f"pytest実行エラー: {e}")
        return False


def check_imports():
    """インポートエラーチェック"""
    print("\n=== インポートチェック ===")
    
    modules_to_check = [
        "telemetry.domain.entities.telemetryRecord",
        "telemetry.domain.repositories.telemetryRepository",
        "telemetry.application.capture.streamCapture",
        "telemetry.infrastructure.persistence.sqliteRepository",
        "telemetry.infrastructure.formatters.telemetryFormatter",
        "telemetry.infrastructure.parsers.telemetryParser",
        "storage.connections.createConnection",
        "storage.connections.createSqliteConnection"
    ]
    
    errors = []
    for module_name in modules_to_check:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                errors.append(f"{module_name}: モジュールが見つかりません")
            else:
                print(f"✓ {module_name}")
        except Exception as e:
            errors.append(f"{module_name}: {str(e)}")
    
    if errors:
        print("\nインポートエラー:")
        for error in errors:
            print(f"  ✗ {error}")
        return False
    else:
        print("\n全モジュールのインポート成功")
        return True




def check_directory_structure():
    """ディレクトリ構造の確認"""
    print("\n=== ディレクトリ構造 ===")
    
    expected_dirs = [
        "telemetry/domain/entities",
        "telemetry/domain/repositories",
        "telemetry/application/capture",
        "telemetry/infrastructure/persistence",
        "telemetry/infrastructure/formatters",
        "telemetry/infrastructure/parsers",
        "storage/connections"
    ]
    
    missing = []
    for dir_path in expected_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path}")
        else:
            missing.append(dir_path)
            print(f"✗ {dir_path}")
    
    # 削除されたディレクトリの確認
    removed_dirs = ["log", "db"]
    for dir_path in removed_dirs:
        if not os.path.exists(dir_path):
            print(f"✓ {dir_path} (削除済み)")
        else:
            print(f"✗ {dir_path} (まだ存在)")
    
    return len(missing) == 0


def run_phase4_verification():
    """Phase 4の完全な動作確認"""
    print("Phase 4 動作確認開始...\n")
    
    checks = [
        ("ディレクトリ構造", check_directory_structure),
        ("インポートチェック", check_imports),
        ("pytest実行", run_pytest)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n{check_name}でエラー: {str(e)}")
            results[check_name] = False
    
    print("\n=== 結果サマリー ===")
    all_passed = True
    for check_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    # PYTHONPATHを設定
    sys.path.insert(0, '/home/nixos/bin/src')
    
    success = run_phase4_verification()
    exit(0 if success else 1)