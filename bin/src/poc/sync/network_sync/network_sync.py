"""
KuzuDB Network Sync POC
実際のネットワーク環境での競合解決と同期をテスト
"""

from typing import List, Dict, Optional, TypedDict, Callable, Set
from datetime import datetime
from enum import Enum
import time
import json


# ========== 型定義 ==========

class NodeState(TypedDict):
    """ノードの状態"""
    node_id: str
    last_sync_timestamp: Optional[str]
    pending_queries: List[str]
    connection_state: str  # "connected" | "disconnected" | "syncing"


class SyncMessage(TypedDict):
    """同期メッセージ"""
    from_node: str
    to_node: str
    queries: List[Dict[str, str]]  # [{query, timestamp, id}]
    vector_clock: Dict[str, int]
    sequence_number: int


class ConflictResolution(TypedDict):
    """競合解決結果"""
    accepted_queries: List[str]
    rejected_queries: List[str]
    reordered_queries: List[str]
    conflict_count: int


class NetworkCondition(Enum):
    """ネットワーク状態"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SLOW = "slow"
    PACKET_LOSS = "packet_loss"
    PARTITIONED = "partitioned"


# ========== REDフェーズテスト: ネットワーク分断と再接続 ==========

def test_handle_network_disconnection_分断時のローカル書き込み():
    """ネットワーク分断中もローカル書き込みが可能"""
    node = NetworkSyncNode("node1")
    
    # 接続中に書き込み
    node.execute_query("CREATE (u:User {id: 1})")
    assert node.get_connection_state() == "connected"
    
    # ネットワーク分断
    node.disconnect()
    assert node.get_connection_state() == "disconnected"
    
    # 分断中もローカル書き込み可能
    node.execute_query("CREATE (u:User {id: 2})")
    node.execute_query("CREATE (u:User {id: 3})")
    
    # ペンディングクエリが蓄積される
    assert len(node.get_pending_queries()) == 2
    assert node.get_local_query_count() == 3


def test_automatic_reconnection_自動再接続():
    """切断後の自動再接続と同期"""
    node1 = NetworkSyncNode("node1")
    node2 = NetworkSyncNode("node2")
    network = NetworkSimulator([node1, node2])
    
    # 初期状態で接続
    network.connect_nodes(node1, node2)
    
    # node1で書き込み後、切断
    node1.execute_query("CREATE (u:User {id: 1})")
    network.disconnect_nodes(node1, node2)
    
    # 切断中の書き込み
    node1.execute_query("CREATE (u:User {id: 2})")
    node2.execute_query("CREATE (p:Product {id: 1})")
    
    # 再接続
    network.reconnect_nodes(node1, node2)
    
    # 自動的に同期される
    assert node1.wait_for_sync(timeout=5) == True
    assert node2.wait_for_sync(timeout=5) == True
    assert node1.get_query_count() == node2.get_query_count()


def test_partial_network_partition_部分的なネットワーク分断():
    """3ノード環境での部分的な分断"""
    node1 = NetworkSyncNode("node1")
    node2 = NetworkSyncNode("node2")
    node3 = NetworkSyncNode("node3")
    network = NetworkSimulator([node1, node2, node3])
    
    # 全ノード接続
    network.connect_all()
    
    # node1とnode2の間だけ切断
    network.disconnect_nodes(node1, node2)
    
    # 各ノードで書き込み
    node1.execute_query("CREATE (u:User {id: 1})")
    node2.execute_query("CREATE (u:User {id: 2})")
    node3.execute_query("CREATE (u:User {id: 3})")
    
    # node3は両方と通信可能なので、最終的に全データを持つ
    node3.wait_for_sync()
    assert node3.get_query_count() == 3
    
    # node1とnode2を再接続
    network.reconnect_nodes(node1, node2)
    
    # 最終的に全ノードが同じ状態に
    assert node1.get_query_count() == 3
    assert node2.get_query_count() == 3


# ========== REDフェーズテスト: メッセージ順序と信頼性 ==========

def test_message_ordering_保証():
    """メッセージの順序保証"""
    sender = NetworkSyncNode("sender")
    receiver = NetworkSyncNode("receiver")
    
    # 順番に送信
    messages = []
    for i in range(5):
        msg = sender.send_query(f"CREATE (u:User {{id: {i}}})")
        messages.append(msg)
    
    # 受信側で順序を確認
    received = receiver.receive_messages()
    assert len(received) == 5
    for i, msg in enumerate(received):
        assert msg.sequence_number == i + 1


def test_handle_packet_loss_パケットロス対策():
    """パケットロスがあっても最終的に同期"""
    node1 = NetworkSyncNode("node1")
    node2 = NetworkSyncNode("node2")
    network = NetworkSimulator([node1, node2])
    
    # 30%のパケットロスを設定
    network.set_packet_loss(0.3)
    
    # 複数のクエリを送信
    for i in range(10):
        node1.execute_query(f"CREATE (u:User {{id: {i}}})")
    
    # 再送により最終的に全て到達
    success = node2.wait_for_query_count(10, timeout=30)
    assert success == True
    assert node2.get_query_count() == 10


def test_handle_duplicate_messages_重複メッセージ除去():
    """ネットワーク再送による重複メッセージを除去"""
    node = NetworkSyncNode("node1")
    
    # 同じメッセージを複数回受信
    msg = SyncMessage(
        from_node="node2",
        to_node="node1",
        queries=[{"query": "CREATE (u:User {id: 1})", "timestamp": "2024-01-01T00:00:00", "id": "msg1"}],
        vector_clock={"node2": 1},
        sequence_number=1
    )
    
    node.receive_message(msg)
    node.receive_message(msg)  # 重複
    node.receive_message(msg)  # 重複
    
    # クエリは1回だけ適用される
    assert node.get_query_count() == 1


# ========== REDフェーズテスト: 競合解決 ==========

def test_concurrent_writes_同時書き込みの解決():
    """同じデータへの同時書き込みを解決"""
    node1 = NetworkSyncNode("node1", conflict_strategy="last_write_wins")
    node2 = NetworkSyncNode("node2", conflict_strategy="last_write_wins")
    
    # ネットワーク分断中に同じIDのユーザーを作成
    node1.disconnect()
    node2.disconnect()
    
    node1.execute_query("CREATE (u:User {id: 1, name: 'Alice'})")
    node2.execute_query("CREATE (u:User {id: 1, name: 'Bob'})")
    
    # 再接続して同期
    sync_result = node1.sync_with(node2)
    
    assert sync_result["conflict_count"] == 1
    assert len(sync_result["accepted_queries"]) == 1
    assert len(sync_result["rejected_queries"]) == 1


def test_vector_clock_causality_因果関係の保持():
    """ベクタークロックによる因果関係の保持"""
    node1 = NetworkSyncNode("node1")
    node2 = NetworkSyncNode("node2")
    node3 = NetworkSyncNode("node3")
    
    # node1 -> node2 -> node3の順で伝播
    node1.execute_query("CREATE (u:User {id: 1})")
    sync_1_to_2 = node1.sync_with(node2)
    
    node2.execute_query("CREATE (r:Relation {from: 1, to: 2})")
    sync_2_to_3 = node2.sync_with(node3)
    
    # node3はnode1の更新も含む
    assert node3.has_query("CREATE (u:User {id: 1})")
    assert node3.get_vector_clock()["node1"] > 0


def test_conflict_free_merge_競合のないマージ():
    """異なるデータへの書き込みは競合なくマージ"""
    node1 = NetworkSyncNode("node1")
    node2 = NetworkSyncNode("node2")
    
    # 別々のデータを作成
    node1.execute_query("CREATE (u:User {id: 1})")
    node1.execute_query("CREATE (u:User {id: 2})")
    
    node2.execute_query("CREATE (p:Product {id: 1})")
    node2.execute_query("CREATE (p:Product {id: 2})")
    
    # マージ
    result = node1.sync_with(node2)
    
    assert result["conflict_count"] == 0
    assert node1.get_query_count() == 4
    assert node2.get_query_count() == 4


# ========== REDフェーズテスト: 効率的な同期 ==========

def test_incremental_sync_差分同期():
    """最後の同期以降の差分のみ送信"""
    node1 = NetworkSyncNode("node1")
    node2 = NetworkSyncNode("node2")
    
    # 初回同期
    node1.execute_query("CREATE (u:User {id: 1})")
    first_sync = node1.sync_with(node2)
    assert first_sync["transferred_queries"] == 1
    
    # 追加の書き込み
    node1.execute_query("CREATE (u:User {id: 2})")
    node1.execute_query("CREATE (u:User {id: 3})")
    
    # 差分同期（2つのクエリのみ転送）
    second_sync = node1.sync_with(node2)
    assert second_sync["transferred_queries"] == 2


def test_checkpoint_recovery_チェックポイントからの回復():
    """チェックポイントを使った効率的な再同期"""
    node1 = NetworkSyncNode("node1")
    node2 = NetworkSyncNode("node2")
    
    # 大量のデータを同期
    for i in range(100):
        node1.execute_query(f"CREATE (u:User {{id: {i}}})")
    
    # チェックポイント作成
    checkpoint = node1.create_checkpoint()
    node1.sync_with(node2)
    
    # node2がクラッシュして再起動
    node2_new = NetworkSyncNode("node2")
    
    # チェックポイントから高速リカバリ
    recovery_result = node2_new.recover_from_checkpoint(checkpoint, node1)
    assert recovery_result["success"] == True
    assert node2_new.get_query_count() == 100


# ========== 実行用コード ==========

if __name__ == "__main__":
    print("=== KuzuDB Network Sync - TDD RED PHASE ===\n")
    
    tests = [
        # ネットワーク分断と再接続
        test_handle_network_disconnection_分断時のローカル書き込み,
        test_automatic_reconnection_自動再接続,
        test_partial_network_partition_部分的なネットワーク分断,
        # メッセージ順序と信頼性
        test_message_ordering_保証,
        test_handle_packet_loss_パケットロス対策,
        test_handle_duplicate_messages_重複メッセージ除去,
        # 競合解決
        test_concurrent_writes_同時書き込みの解決,
        test_vector_clock_causality_因果関係の保持,
        test_conflict_free_merge_競合のないマージ,
        # 効率的な同期
        test_incremental_sync_差分同期,
        test_checkpoint_recovery_チェックポイントからの回復,
    ]
    
    failed = 0
    for test in tests:
        print(f"実行中: {test.__name__}")
        try:
            test()
            print("  ✗ テストが成功しました（実装が既に存在？）")
        except NameError as e:
            print(f"  ✓ RED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✓ RED: {type(e).__name__}: {e}")
            failed += 1
        print()
    
    print(f"=== 結果: {failed}/{len(tests)} テストが期待通り失敗 ===")