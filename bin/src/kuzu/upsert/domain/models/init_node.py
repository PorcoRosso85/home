"""
初期化ノードモデル

このモジュールでは、初期化データ（CONVENTION.yaml等）のノードを表現するドメインモデルを定義します。
"""

from typing import Dict, Any, List, Optional
from upsert.domain.types import Entity


class InitNode(Entity):
    """初期化データのノードを表現するエンティティ

    すべてのキー（パス）とその値をノードとして扱います。
    """
    
    def __init__(
        self,
        id: str,
        path: str,
        label: str,
        value: Optional[str] = None,
        value_type: Optional[str] = None
    ):
        """
        Args:
            id: ノードのID
            path: YAMLのパス（ドット区切りのキーの連鎖）
            label: ノードのラベル（パスの最後の部分）
            value: ノードが持つ値（リーフノードの場合）
            value_type: 値の型（string, number, boolean, array, object, null）
        """
        self.id = id
        self.path = path
        self.label = label
        self.value = value
        self.value_type = value_type
        
    def is_leaf(self) -> bool:
        """このノードがリーフノード（値を持つ）かどうかを返す"""
        return self.value is not None or self.value_type == "null"


# 単体テスト
def test_init_node() -> None:
    """InitNodeのテスト"""
    # キーノードのテスト
    key_node = InitNode(
        id="common.基本原則",
        path="common.基本原則",
        label="基本原則"
    )
    assert key_node.id == "common.基本原則"
    assert key_node.path == "common.基本原則"
    assert key_node.label == "基本原則"
    assert key_node.value is None
    assert key_node.value_type is None
    assert not key_node.is_leaf()
    
    # 値ノードのテスト
    value_node = InitNode(
        id="common.基本原則.クラス使用",
        path="common.基本原則.クラス使用",
        label="クラス使用",
        value="可能ならクラスは使わない",
        value_type="string"
    )
    assert value_node.id == "common.基本原則.クラス使用"
    assert value_node.path == "common.基本原則.クラス使用"
    assert value_node.label == "クラス使用"
    assert value_node.value == "可能ならクラスは使わない"
    assert value_node.value_type == "string"
    assert value_node.is_leaf()
