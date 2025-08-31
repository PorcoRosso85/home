#!/usr/bin/env python3
"""Interactive Transport Test - 長時間実行版"""

import time
import sys
from mod import SessionManager

def interactive_test():
    """対話的テスト"""
    print("=== Transport Interactive Test ===")
    print("Starting sessions and keeping them alive...")
    print()
    
    manager = SessionManager()
    
    # セッション1を起動
    print("Starting session 1...")
    session1 = manager.get_or_create_session(1)
    print(f"Session 1: {session1.work_dir}")
    
    time.sleep(5)
    
    # セッション2を起動  
    print("\nStarting session 2...")
    session2 = manager.get_or_create_session(2)
    print(f"Session 2: {session2.work_dir}")
    
    print("\n--- Sessions Ready ---")
    print("Commands:")
    print("  1 <cmd>  - Send to session 1")
    print("  2 <cmd>  - Send to session 2")
    print("  status   - Show session status")
    print("  quit     - Exit")
    print()
    
    try:
        while True:
            cmd = input("> ").strip()
            
            if cmd == "quit":
                break
            elif cmd == "status":
                status = manager.get_status()
                for sid, state in status.items():
                    print(f"  Session {sid}: {state}")
            elif cmd.startswith("1 "):
                manager.send_to(1, cmd[2:])
            elif cmd.startswith("2 "):
                manager.send_to(2, cmd[2:])
            else:
                print("Unknown command")
                
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        print("\nClosing sessions...")
        manager.close_all()
        print("Done")

if __name__ == "__main__":
    interactive_test()