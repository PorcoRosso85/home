#!/usr/bin/env python3
"""シンプルなテスト実行スクリプト（REDフェーズ確認用）"""

# テストをインポートして実行を試みる
try:
    from auth_graph import AuthGraph
    print("❌ ERROR: AuthGraph should not exist yet (we're in RED phase)")
except ImportError:
    print("✅ GOOD: AuthGraph does not exist (expected in RED phase)")

# テストファイルから直接テスト関数を実行
import sys
sys.path.append('tests')

try:
    import test_grant_permission
    print("\n✅ Test file can be imported")
    
    # テストを実行してみる
    try:
        test_grant_permission.test_grant_permission_creates_auth_relationship()
        print("❌ ERROR: Test should fail but it passed")
    except Exception as e:
        print(f"✅ GOOD: Test failed as expected - {type(e).__name__}: {e}")
        
except Exception as e:
    print(f"\n❌ Cannot import test file: {e}")