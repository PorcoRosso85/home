#!/usr/bin/env python3
"""
メインエントリーポイント（絶対パスインポート版）
"""

# 絶対パスでのインポート（プロジェクトルートからのパス）
from examples.absolute_imports.domain.user import User
from examples.absolute_imports.infrastructure.database import Database
from examples.absolute_imports.application.user_service import UserService


def main():
    """アプリケーションのメイン処理"""
    # 依存性の構築
    db = Database()
    service = UserService(db)
    
    # ユーザー作成
    user = User("alice", "alice@example.com")
    saved_user = service.save_user(user)
    
    print(f"Saved user: {saved_user}")
    
    # ユーザー取得
    found = service.find_by_name("alice")
    if found:
        print(f"Found user: {found}")


if __name__ == "__main__":
    main()