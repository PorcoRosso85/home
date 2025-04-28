"""
初期化エッジモデル

このモジュールでは、初期化データ（CONVENTION.yaml等）のノード間の関係を表現するエッジモデルを定義します。
"""

from typing import Optional
from upsert.domain.types import Relationship


class InitEdge(Relationship):
    """初期化データのノード間の関係を表現するエッジ

    親ノードと子ノードの間の「具体化」関係を表します。
    """
    
    def __init__(
        self,
        id: str,
        source_id: str,
        target_id: str,
        relation_type: str = "concretizes"
    ):
        """
        Args:
            id: エッジのID
            source_id: 親ノードのID
            target_id: 子ノードのID
            relation_type: 関係タイプ（デフォルトは具体化"concretizes"）
        """
        self.id = id
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type


# 単体テスト
def test_init_edge() -> None:
    """InitEdgeのテスト"""
    # 基本的な具体化エッジのテスト
    edge = InitEdge(
        id="common.基本原則->common.基本原則.クラス使用",
        source_id="common.基本原則",
        target_id="common.基本原則.クラス使用"
    )
    assert edge.id == "common.基本原則->common.基本原則.クラス使用"
    assert edge.source_id == "common.基本原則"
    assert edge.target_id == "common.基本原則.クラス使用"
    assert edge.relation_type == "concretizes"
    
    # カスタム関係タイプのテスト
    custom_edge = InitEdge(
        id="common->python",
        source_id="common",
        target_id="python",
        relation_type="extends"
    )
    assert custom_edge.id == "common->python"
    assert custom_edge.source_id == "common"
    assert custom_edge.target_id == "python"
    assert custom_edge.relation_type == "extends"
