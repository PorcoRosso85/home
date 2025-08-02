"""
データベース層（インメモリ実装）
"""

from typing import Dict, Optional
# 相対パスでのインポート（親ディレクトリから）
from ..domain.user import User


class Database:
    """シンプルなインメモリデータベース"""
    
    def __init__(self):
        self._storage: Dict[str, User] = {}
    
    def save(self, user: User) -> User:
        """ユーザーを保存"""
        self._storage[user.name] = user
        return user
    
    def find_by_name(self, name: str) -> Optional[User]:
        """名前でユーザーを検索"""
        return self._storage.get(name)