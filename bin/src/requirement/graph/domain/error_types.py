"""
エラー型の定義（ドメイン層）

ユーザーフレンドリーなエラー情報を提供するための型定義
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ErrorExample:
    """エラー修正のための例"""
    description: str
    query: str


@dataclass
class ErrorGuidance:
    """エラー回復のガイダンス"""
    issue: str
    possible_causes: List[str]
    setup_commands: List[str]
    next_action: Optional[str] = None


@dataclass
class UserFriendlyError:
    """ユーザーフレンドリーなエラー情報"""
    error_code: str
    user_message: str
    explanation: str
    suggested_action: str
    examples: List[ErrorExample]
    technical_details: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "type": "error",
            "level": "error",
            "error_code": self.error_code,
            "user_message": self.user_message,
            "explanation": self.explanation,
            "suggested_action": self.suggested_action,
            "examples": [
                {
                    "description": ex.description,
                    "query": ex.query
                } for ex in self.examples
            ],
            "technical_details": self.technical_details,
            "timestamp": self.timestamp
        }


@dataclass
class RecoveryGuidance:
    """エラー回復ガイダンス"""
    error_type: str
    steps: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "recovery_guidance": {
                "steps": self.steps
            }
        }