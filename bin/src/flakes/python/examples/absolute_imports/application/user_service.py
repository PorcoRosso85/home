"""
アプリケーションサービス層
"""

from typing import Optional
# 絶対パスでのインポート
from examples.absolute_imports.domain.user import User
from examples.absolute_imports.infrastructure.database import Database


class UserService:
    """ユーザー関連のビジネスロジック"""
    
    def __init__(self, database: Database):
        self._db = database
    
    def save_user(self, user: User) -> User:
        """ユーザーを保存"""
        # ビジネスルール：同名のユーザーは保存できない
        existing = self._db.find_by_name(user.name)
        if existing:
            raise ValueError(f"User with name '{user.name}' already exists")
        
        return self._db.save(user)
    
    def find_by_name(self, name: str) -> Optional[User]:
        """名前でユーザーを検索"""
        return self._db.find_by_name(name)