#!/usr/bin/env python3
"""セッション間通信テスト"""

import time
from mod import SessionManager

def test_communication():
    """1.1と1.2の通信テスト"""
    print("=== Transport Communication Test ===")
    print()
    
    manager = SessionManager()
    
    # セッション1に接続（1.1のClaude）
    print("Connecting to session 1 (pane 1.1)...")
    s1 = manager.get_or_create_session(1)
    print(f"Session 1 alive: {s1.is_ready()}")
    
    # セッション2に接続（1.2のClaude）  
    print("\nConnecting to session 2 (pane 1.2)...")
    s2 = manager.get_or_create_session(2)
    print(f"Session 2 alive: {s2.is_ready()}")
    
    # セッション1にコマンド送信
    print("\n--- Sending to Session 1 ---")
    s1.send_command("echo '[Session 1] Received message from transport'")
    time.sleep(2)
    
    # セッション2にコマンド送信
    print("\n--- Sending to Session 2 ---")
    s2.send_command("echo '[Session 2] Received message from transport'")
    time.sleep(2)
    
    # 複数コマンド送信
    print("\n--- Multiple Commands ---")
    s1.send_command("pwd")
    s2.send_command("ls")
    
    print("\n=== Test Complete ===")
    print(f"Both sessions active: {s1.is_ready() and s2.is_ready()}")

if __name__ == "__main__":
    test_communication()