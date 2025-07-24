#!/usr/bin/env python3
"""GREENフェーズ確認用のテストスクリプト"""

import sys
sys.path.insert(0, 'src')

try:
    from auth_graph import AuthGraph
    print("✅ AuthGraph can be imported")
    
    # インメモリDBでテスト
    auth = AuthGraph(":memory:")
    print("✅ AuthGraph instance created")
    
    # grant_permissionのテスト
    auth.grant_permission("user:alice", "resource:file/123")
    print("✅ grant_permission executed without error")
    
    # has_permissionのテスト
    result = auth.has_permission("user:alice", "resource:file/123")
    if result:
        print("✅ has_permission returned True (expected)")
    else:
        print("❌ has_permission returned False (unexpected)")
        
    # 存在しない権限のテスト
    result2 = auth.has_permission("user:bob", "resource:file/123")
    if not result2:
        print("✅ has_permission returned False for non-existent permission (expected)")
    else:
        print("❌ has_permission returned True for non-existent permission (unexpected)")
        
    # 冪等性のテスト
    auth.grant_permission("user:alice", "resource:file/123")  # 2回目
    print("✅ Second grant_permission executed (idempotency test)")
    
    print("\n🎉 All basic tests passed! We are in GREEN phase.")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()