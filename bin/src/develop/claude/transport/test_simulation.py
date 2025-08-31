#!/usr/bin/env python3
"""Transport Module Simulation Test"""

import time
import subprocess
from pathlib import Path
from mod import SessionManager

def run_simulation():
    """シミュレーションテスト実行"""
    print("=== Transport Module Simulation Test ===")
    print()
    
    manager = SessionManager()
    
    # Test 1: セッション1を起動
    print("Test 1: Starting session 1...")
    try:
        session1 = manager.get_or_create_session(1)
        print(f"✓ Session 1 started at {session1.work_dir}")
        print(f"  JSONL: {session1.jsonl_path}")
    except Exception as e:
        print(f"✗ Failed to start session 1: {e}")
        return
    
    time.sleep(3)  # Claude起動待機
    
    # Test 2: コマンド送信
    print("\nTest 2: Sending command to session 1...")
    success = manager.send_to(1, "pwd")
    print(f"✓ Command sent: {'Success' if success else 'Failed'}")
    
    time.sleep(2)
    
    # Test 3: セッション2を起動
    print("\nTest 3: Starting session 2...")
    try:
        session2 = manager.get_or_create_session(2)
        print(f"✓ Session 2 started at {session2.work_dir}")
        print(f"  JSONL: {session2.jsonl_path}")
    except Exception as e:
        print(f"✗ Failed to start session 2: {e}")
    
    time.sleep(3)
    
    # Test 4: 複数セッションへの送信
    print("\nTest 4: Sending to multiple sessions...")
    manager.send_to(1, "echo 'Hello from manager'")
    time.sleep(1)
    manager.send_to(2, "echo 'Test from session 2'")
    
    # Test 5: ステータス確認
    print("\nTest 5: Checking status...")
    status = manager.get_status()
    for sid, state in status.items():
        print(f"  Session {sid}: {state}")
    
    # Test 6: JSONL確認
    print("\nTest 6: Checking JSONL entries...")
    for sid, session in manager.sessions.items():
        entry = session.get_latest_entry()
        if entry:
            print(f"  Session {sid} latest: {entry.get('type', 'unknown')}")
        else:
            print(f"  Session {sid}: No JSONL entry")
    
    # Clean up
    print("\nCleaning up...")
    manager.close_all()
    print("✓ All sessions closed")
    
    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    run_simulation()