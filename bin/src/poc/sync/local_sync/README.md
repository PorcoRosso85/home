# KuzuDB Distributed Sync Engine

複数のKuzuDBインスタンス（特にWASM環境）間でグラフデータベースの完全同期を実現するエンジン。

## 背景と課題

- **課題**: エッジデバイス上の複数KuzuDBインスタンスが独立して動作し、データの一貫性が保証されない
- **要求**: オフライン対応、最終的一貫性、競合の自動解決
- **制約**: WASM環境のメモリ制限（通常32-128MB）、ネットワーク断続

## 仕様（TDDで証明）

### 1. イベント同期プロトコル

```python
def test_sync_protocol_initialization():
    """同期プロトコルの初期化とハンドシェイク"""
    node_a = create_sync_node("node_a")
    node_b = create_sync_node("node_b")
    
    # ハンドシェイク
    session = node_a.initiate_sync(node_b.endpoint)
    assert session.status == "established"
    assert session.protocol_version == "1.0"
    assert session.sync_mode == "incremental"

def test_event_exchange_with_vector_clock():
    """ベクタークロックを使用したイベント交換"""
    event_a = {
        "id": "evt_a1",
        "vector_clock": {"node_a": 1, "node_b": 0},
        "operation": "add_node",
        "data": {"label": "User", "properties": {"name": "Alice"}}
    }
    
    sync_result = sync_events([event_a], target_node="node_b")
    assert sync_result.applied_count == 1
    assert sync_result.vector_clock["node_a"] == 1
    assert sync_result.vector_clock["node_b"] == 1
```

### 2. 競合検出と解決

```python
def test_concurrent_modification_conflict():
    """同一ノードへの同時変更の検出と解決"""
    # Node Aでの変更
    event_a = {
        "node_id": "user_123",
        "operation": "update_property",
        "property": "email",
        "value": "alice@a.com",
        "timestamp": "2024-01-01T10:00:00Z",
        "vector_clock": {"node_a": 2, "node_b": 1}
    }
    
    # Node Bでの変更
    event_b = {
        "node_id": "user_123",
        "operation": "update_property", 
        "property": "email",
        "value": "alice@b.com",
        "timestamp": "2024-01-01T10:00:01Z",
        "vector_clock": {"node_a": 1, "node_b": 2}
    }
    
    conflict = detect_conflict(event_a, event_b)
    assert conflict.type == "concurrent_update"
    assert conflict.resolution_strategy == "last_write_wins"
    
    resolved = resolve_conflict(conflict)
    assert resolved.winning_value == "alice@b.com"  # タイムスタンプが新しい

def test_semantic_conflict_resolution():
    """セマンティックな競合解決（カウンタのマージなど）"""
    # 在庫数の同時更新
    event_a = {"op": "increment", "field": "stock", "delta": -5}  # 5個販売
    event_b = {"op": "increment", "field": "stock", "delta": -3}  # 3個販売
    
    resolved = resolve_semantic_conflict(event_a, event_b, strategy="cumulative")
    assert resolved.final_delta == -8  # 両方の変更を累積
```

### 3. 分散トランザクション

```python
def test_distributed_transaction_2pc():
    """2フェーズコミットによる分散トランザクション"""
    coordinator = create_coordinator()
    participants = [create_node(f"node_{i}") for i in range(3)]
    
    # トランザクション開始
    tx = coordinator.begin_transaction()
    
    # 各ノードに操作を送信
    prepare_results = []
    for node in participants:
        result = node.prepare(tx.id, operations=[
            {"op": "create_edge", "from": "user_1", "to": "user_2", "type": "FOLLOWS"}
        ])
        prepare_results.append(result)
    
    assert all(r.vote == "commit" for r in prepare_results)
    
    # コミット
    commit_results = coordinator.commit(tx.id)
    assert all(r.status == "committed" for r in commit_results)

def test_distributed_transaction_rollback():
    """失敗時の分散ロールバック"""
    tx = begin_distributed_transaction()
    
    # 1つのノードが失敗
    prepare_results = [
        {"node": "node_1", "vote": "commit"},
        {"node": "node_2", "vote": "abort", "reason": "disk_full"},
        {"node": "node_3", "vote": "commit"}
    ]
    
    final_result = coordinator.decide(tx.id, prepare_results)
    assert final_result.decision == "abort"
    assert all(node.state == "rolled_back" for node in get_all_nodes())
```

### 4. オフライン同期

```python
def test_offline_operation_queue():
    """オフライン時の操作キューイング"""
    node = create_sync_node("offline_node")
    node.go_offline()
    
    # オフライン中の操作
    operations = [
        node.add_node("User", {"name": "Bob"}),
        node.add_edge("FOLLOWS", "user_1", "user_2"),
        node.update_property("user_1", "status", "active")
    ]
    
    assert node.offline_queue.size() == 3
    assert node.offline_queue.estimated_size_bytes() < 1024 * 1024  # 1MB以下
    
    # オンライン復帰
    node.go_online()
    sync_result = node.sync_offline_changes()
    
    assert sync_result.synced_operations == 3
    assert sync_result.conflicts_resolved == 0
    assert node.offline_queue.size() == 0

def test_offline_conflict_resolution():
    """オフライン変更の競合解決"""
    # Node Aがオフライン中に user_1 を更新
    offline_changes_a = [
        {"node_id": "user_1", "property": "status", "value": "inactive"}
    ]
    
    # 同じ期間にNode Bも user_1 を更新
    online_changes_b = [
        {"node_id": "user_1", "property": "status", "value": "banned"}
    ]
    
    # Node Aがオンライン復帰
    merge_result = merge_offline_changes(offline_changes_a, online_changes_b)
    assert merge_result.conflicts[0].resolution == "online_wins"
    assert get_node_property("user_1", "status") == "banned"
```

### 5. 効率的な差分同期

```python
def test_merkle_tree_diff_sync():
    """Merkleツリーによる効率的な差分検出"""
    node_a = create_node_with_data(node_count=10000)
    node_b = create_node_with_data(node_count=9990)  # 10個の差分
    
    # Merkleツリー構築
    tree_a = build_merkle_tree(node_a)
    tree_b = build_merkle_tree(node_b)
    
    # 差分検出
    diff = compute_merkle_diff(tree_a, tree_b)
    assert len(diff.missing_in_b) == 10
    assert diff.comparison_operations < 100  # 全比較より大幅に少ない
    
    # 差分のみ同期
    sync_result = sync_diff_only(diff, from_node=node_a, to_node=node_b)
    assert sync_result.transferred_nodes == 10
    assert sync_result.bandwidth_used_bytes < 10 * 1024  # 10KB以下

def test_incremental_snapshot_sync():
    """インクリメンタルスナップショットによる同期"""
    # 前回の同期ポイント
    last_sync = {
        "timestamp": "2024-01-01T00:00:00Z",
        "event_count": 1000,
        "checksum": "abc123"
    }
    
    # 新しいイベント（100件）
    new_events = generate_events(100, after=last_sync["timestamp"])
    
    # 差分同期
    sync_result = incremental_sync(last_sync, new_events)
    assert sync_result.events_synced == 100
    assert sync_result.full_resync_required == False
```

### 6. ネットワーク最適化

```python
def test_sync_compression():
    """同期データの圧縮"""
    large_graph_data = generate_large_graph(nodes=1000, edges=5000)
    
    compressed = compress_sync_data(large_graph_data)
    assert compressed.compression_ratio > 0.5  # 50%以上圧縮
    assert compressed.algorithm == "zstd"
    
    decompressed = decompress_sync_data(compressed)
    assert decompressed == large_graph_data

def test_adaptive_sync_strategy():
    """ネットワーク状況に応じた同期戦略の適応"""
    network_quality = measure_network_quality()
    
    if network_quality.bandwidth_mbps < 1:
        strategy = select_sync_strategy(network_quality)
        assert strategy.type == "priority_based"
        assert strategy.sync_critical_only == True
    elif network_quality.latency_ms > 500:
        strategy = select_sync_strategy(network_quality)
        assert strategy.type == "batch_optimized"
        assert strategy.batch_size > 100
```

## 実装アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐
│   Node A        │     │   Node B        │
│  ┌───────────┐  │     │  ┌───────────┐  │
│  │KuzuDB WASM│  │     │  │KuzuDB WASM│  │
│  └───────────┘  │     │  └───────────┘  │
│  ┌───────────┐  │     │  ┌───────────┐  │
│  │Event Log  │  │◄────►│  │Event Log  │  │
│  └───────────┘  │     │  └───────────┘  │
│  ┌───────────┐  │     │  ┌───────────┐  │
│  │Sync Engine│  │     │  │Sync Engine│  │
│  └───────────┘  │     │  └───────────┘  │
└─────────────────┘     └─────────────────┘
         │                       │
         └───────┬───────────────┘
                 │
         ┌───────▼────────┐
         │ Sync Protocol  │
         │   - 2PC        │
         │   - Gossip     │
         │   - Merkle     │
         └────────────────┘
```

## 技術選択

- **同期プロトコル**: CRDTベース + Vector Clock
- **競合解決**: Last Write Wins + Semantic Merging
- **差分検出**: Merkle Tree
- **圧縮**: zstd（WASM対応）
- **永続化**: IndexedDB（ブラウザ）/ SQLite（Node.js）

## パフォーマンス目標

- 1000ノードの差分同期: < 100ms
- メモリ使用量: < 32MB（WASM制約）
- オフラインキュー: 最大10,000操作
- 圧縮率: > 50%
- 競合解決時間: < 10ms/競合