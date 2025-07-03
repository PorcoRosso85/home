# KuzuDB Event Ledger

KuzuDBのすべての変更をイミュータブルなイベントログとして記録し、クラウドストレージ（S3/GCS）に永続化する台帳システム。

## 背景と課題

- **課題**: グラフデータベースの変更履歴が失われ、監査やデバッグが困難
- **要求**: 完全な変更履歴、タイムトラベルクエリ、コンプライアンス対応
- **制約**: ストレージコスト、イベント順序保証、スケーラビリティ

## 仕様（TDDで証明）

### 1. イベントの記録と構造

```python
def test_event_structure_completeness():
    """イベントが必要な全情報を含むことを検証"""
    event = create_graph_event(
        operation="CREATE_NODE",
        label="User",
        properties={"name": "Alice", "email": "alice@example.com"}
    )
    
    assert event["event_id"] is not None  # UUID v7 (時系列ソート可能)
    assert event["timestamp"] is not None  # ISO 8601 with microseconds
    assert event["operation"] in VALID_OPERATIONS
    assert event["actor"] is not None  # 誰が実行したか
    assert event["checksum"] is not None  # SHA-256
    assert event["previous_event_id"] is not None  # チェーン構造
    assert event["partition_key"] is not None  # 効率的なクエリ用

def test_event_immutability():
    """イベントの不変性を保証"""
    event = create_graph_event(operation="UPDATE_NODE", node_id="user_123")
    original_checksum = event["checksum"]
    
    # イベントの改竄を試みる
    event["properties"]["name"] = "Modified"
    
    # チェックサム検証で改竄を検出
    assert verify_event_integrity(event) == False
    assert calculate_checksum(event) != original_checksum

def test_event_chain_integrity():
    """イベントチェーンの整合性検証"""
    events = []
    for i in range(10):
        event = create_graph_event(
            operation=f"OP_{i}",
            previous_event_id=events[-1]["event_id"] if events else None
        )
        events.append(event)
    
    # チェーン検証
    chain_valid = verify_event_chain(events)
    assert chain_valid == True
    
    # チェーンの改竄を検出
    events[5]["previous_event_id"] = "invalid_id"
    assert verify_event_chain(events) == False
```

### 2. クラウドストレージへの永続化

```python
def test_s3_event_storage():
    """S3への効率的なイベント保存"""
    storage = create_s3_event_storage(
        bucket="kuzu-events",
        region="us-east-1"
    )
    
    # 単一イベントの保存
    event = create_graph_event(operation="CREATE_NODE")
    stored = storage.store_event(event)
    
    assert stored.key == f"events/{event['partition_key']}/{event['event_id']}.json"
    assert stored.metadata["checksum"] == event["checksum"]
    assert stored.storage_class == "STANDARD_IA"  # コスト最適化

def test_event_batching_and_compression():
    """イベントのバッチ化と圧縮"""
    events = [create_graph_event(operation=f"OP_{i}") for i in range(1000)]
    
    # バッチ作成（1MBまたは1000イベント）
    batch = create_event_batch(events)
    assert batch.event_count == 1000
    assert batch.compression == "zstd"
    assert batch.size_bytes < batch.uncompressed_size * 0.3  # 70%以上圧縮
    
    # S3への保存
    stored = storage.store_batch(batch)
    assert stored.key.endswith(".batch.zst")
    assert stored.metadata["event_count"] == "1000"
    assert stored.metadata["time_range"] == f"{events[0]['timestamp']}/{events[-1]['timestamp']}"

def test_partitioning_strategy():
    """時系列とアクセスパターンに基づくパーティショニング"""
    # 日付ベースのパーティション
    event = create_graph_event(timestamp="2024-01-15T10:30:00Z")
    partition = calculate_partition(event)
    
    assert partition.year == "2024"
    assert partition.month == "01"
    assert partition.day == "15"
    assert partition.hour == "10"
    assert partition.path == "events/2024/01/15/10/"
    
    # ホットパーティションの検出
    hot_partitions = detect_hot_partitions(time_window="1h")
    assert len(hot_partitions) > 0
    assert hot_partitions[0].writes_per_second > 100
```

### 3. イベントストリーミング

```python
def test_event_streaming_interface():
    """リアルタイムイベントストリーミング"""
    stream = create_event_stream(
        source="s3://kuzu-events/",
        start_time="2024-01-01T00:00:00Z"
    )
    
    # ストリーム読み取り
    events = []
    for event in stream.read(limit=100):
        events.append(event)
        assert event["timestamp"] >= "2024-01-01T00:00:00Z"
    
    assert len(events) == 100
    assert stream.position.offset > 0
    assert stream.position.partition is not None

def test_stream_checkpoint_resume():
    """ストリーム処理の中断と再開"""
    stream = create_event_stream()
    
    # 50イベント処理後にチェックポイント
    processed = 0
    for event in stream.read():
        process_event(event)
        processed += 1
        if processed == 50:
            checkpoint = stream.create_checkpoint()
            break
    
    # チェックポイントから再開
    resumed_stream = resume_from_checkpoint(checkpoint)
    assert resumed_stream.position == checkpoint.position
    
    # 次のイベントから処理継続
    next_event = next(resumed_stream.read())
    assert next_event["event_id"] != checkpoint.last_event_id

def test_parallel_stream_processing():
    """並列ストリーム処理"""
    # 4つのパーティションを並列処理
    partitions = get_stream_partitions(count=4)
    results = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for partition in partitions:
            future = executor.submit(process_partition, partition)
            futures.append(future)
        
        for future in futures:
            result = future.result()
            results.append(result)
    
    # 全パーティションが処理されたことを確認
    total_events = sum(r.event_count for r in results)
    assert total_events == get_total_event_count()
    assert all(r.errors == 0 for r in results)
```

### 4. 効率的なクエリ

```python
def test_time_range_query():
    """時間範囲クエリの効率性"""
    query = create_time_range_query(
        start="2024-01-01T00:00:00Z",
        end="2024-01-01T01:00:00Z"
    )
    
    # インデックスを使用した効率的なスキャン
    result = execute_query(query)
    assert result.partitions_scanned <= 2  # 最大2パーティション
    assert result.execution_time_ms < 100
    assert all(e["timestamp"] >= query.start for e in result.events)
    assert all(e["timestamp"] <= query.end for e in result.events)

def test_entity_history_query():
    """特定エンティティの変更履歴取得"""
    history = get_entity_history(
        entity_type="NODE",
        entity_id="user_123",
        include_related=True
    )
    
    assert len(history.events) > 0
    assert history.events[0]["operation"] == "CREATE_NODE"
    assert history.events[-1]["timestamp"] <= datetime.now().isoformat()
    
    # 関連エッジの変更も含む
    edge_events = [e for e in history.events if e["entity_type"] == "EDGE"]
    assert len(edge_events) > 0

def test_aggregate_query():
    """集計クエリの実行"""
    # 過去24時間の操作統計
    stats = get_operation_statistics(
        time_window="24h",
        group_by=["operation", "hour"]
    )
    
    assert stats.total_operations > 0
    assert "CREATE_NODE" in stats.by_operation
    assert len(stats.by_hour) == 24
    assert stats.peak_hour is not None
    assert stats.cache_hit_rate > 0.8  # 80%以上のキャッシュヒット率
```

### 5. コンプライアンスとセキュリティ

```python
def test_audit_trail_completeness():
    """監査証跡の完全性"""
    audit_trail = generate_audit_trail(
        entity_id="sensitive_user_123",
        time_range="last_year"
    )
    
    # 全操作が記録されている
    assert audit_trail.has_gaps == False
    assert audit_trail.events[0]["operation"] == "CREATE_NODE"
    
    # PII操作の特別な記録
    pii_operations = [e for e in audit_trail.events if e.get("pii_affected")]
    assert all(e["actor"] is not None for e in pii_operations)
    assert all(e["justification"] is not None for e in pii_operations)

def test_gdpr_compliance():
    """GDPR準拠のデータ処理"""
    # データ削除要求
    deletion_request = create_gdpr_deletion_request(user_id="user_123")
    
    # 論理削除マーカーの追加
    deletion_event = create_deletion_event(deletion_request)
    assert deletion_event["operation"] == "GDPR_DELETE"
    assert deletion_event["retained_fields"] == ["id"]  # IDのみ保持
    
    # 削除後のクエリ
    history = get_entity_history("NODE", "user_123")
    assert all(e.get("pii_masked") == True for e in history.events)

def test_encryption_at_rest():
    """保存時の暗号化"""
    event = create_graph_event(
        operation="UPDATE_NODE",
        properties={"ssn": "123-45-6789"}  # 機密データ
    )
    
    # 暗号化して保存
    encrypted = encrypt_event(event, kms_key_id="arn:aws:kms:...")
    assert encrypted.ciphertext != json.dumps(event)
    assert encrypted.metadata["encryption_context"]["event_id"] == event["event_id"]
    
    # 復号化
    decrypted = decrypt_event(encrypted)
    assert decrypted == event
```

### 6. 自動アーカイブとライフサイクル

```python
def test_automatic_archival():
    """古いイベントの自動アーカイブ"""
    lifecycle_policy = create_lifecycle_policy(
        hot_duration_days=7,
        warm_duration_days=30,
        cold_duration_days=365
    )
    
    # 7日以上前のイベントをwarmストレージへ
    archived = apply_lifecycle_policy(lifecycle_policy)
    assert archived.moved_to_warm > 0
    assert archived.moved_to_cold > 0
    assert archived.cost_savings_percent > 50

def test_archive_retrieval():
    """アーカイブからの取得"""
    # Glacierからの取得リクエスト
    retrieval_request = request_archive_retrieval(
        time_range="2023-01-01/2023-01-31",
        priority="expedited"  # 1-5分で取得
    )
    
    assert retrieval_request.status == "initiated"
    assert retrieval_request.estimated_completion_time < 5 * 60  # 5分以内
    
    # 取得完了後
    retrieved_events = get_retrieved_events(retrieval_request.id)
    assert len(retrieved_events) > 0
    assert all(e["timestamp"].startswith("2023-01") for e in retrieved_events)
```

## 実装アーキテクチャ

```
┌──────────────┐        ┌─────────────────┐
│  KuzuDB      │        │  Event Buffer   │
│  Instance    │──────► │  (In-Memory)    │
└──────────────┘        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  Event Writer   │
                        │  - Validation   │
                        │  - Compression  │
                        │  - Batching     │
                        └────────┬────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
        │   S3/GCS     │ │  Kinesis/   │ │  Search     │
        │  (Primary)   │ │  PubSub     │ │  Index      │
        └──────────────┘ └─────────────┘ └─────────────┘
                │
        ┌───────┴────────────────┐
        │                        │
┌───────▼──────┐        ┌───────▼──────┐
│   Hot Tier   │        │  Warm Tier   │
│  (STANDARD)  │        │ (STANDARD_IA)│
└──────────────┘        └───────┬──────┘
                                │
                        ┌───────▼──────┐
                        │  Cold Tier   │
                        │  (GLACIER)   │
                        └──────────────┘
```

## 技術選択

- **ストレージ**: S3/GCS with lifecycle policies
- **ストリーミング**: Kinesis Data Streams / Google Pub/Sub
- **圧縮**: zstd (最高の圧縮率/速度バランス)
- **暗号化**: AWS KMS / Google Cloud KMS
- **インデックス**: DynamoDB / Firestore (メタデータ)
- **フォーマット**: JSON Lines (.jsonl) for streaming

## パフォーマンス目標

- イベント書き込みレイテンシ: < 10ms (バッファ経由)
- バッチサイズ: 1MB または 1000イベント
- 圧縮率: > 70%
- クエリレイテンシ: < 100ms (インデックス使用時)
- ストリーミングスループット: > 10,000 events/秒
- ストレージコスト: < $0.01/GB/月 (ライフサイクル適用後)