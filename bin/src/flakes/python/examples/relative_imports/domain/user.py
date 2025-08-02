"""
ユーザードメインモデル
"""

from dataclasses import dataclass


@dataclass
class User:
    """ユーザーエンティティ"""
    name: str
    email: str
    
    def __post_init__(self):
        """バリデーション"""
        if not self.name:
            raise ValueError("Name cannot be empty")
        if "@" not in self.email:
            raise ValueError("Invalid email format")