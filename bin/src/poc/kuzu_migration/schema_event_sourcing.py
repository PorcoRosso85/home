"""
KuzuDB Schema Event Sourcing
スキーマ変更をイベントとして管理し、マイグレーションを不要にする
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import hashlib


# ========== RED PHASE: 失敗するテストから開始 ==========

def test_create_schema_event_基本機能_イベント生成():
    """スキーマ変更イベントを作成できる"""
    event = create_schema_event(
        event_type="add_field",
        table="users",
        field="email",
        data_type="STRING",
        default=""
    )
    assert event["event_type"] == "schema_change"
    assert event["timestamp"] is not None
    assert event["change"]["type"] == "add_field"
    assert event["change"]["table"] == "users"
    assert event["change"]["field"] == "email"


def test_apply_add_field_フィールド追加_スキーマ更新():
    """フィールド追加をスキーマに適用できる"""
    schema = {"users": {"id": "INT64", "name": "STRING"}}
    change = {
        "type": "add_field",
        "table": "users",
        "field": "email",
        "data_type": "STRING",
        "default": ""
    }
    
    new_schema = apply_add_field(schema, change)
    assert "email" in new_schema["users"]
    assert new_schema["users"]["email"] == "STRING"
    assert new_schema["users"]["id"] == "INT64"  # 既存フィールドは保持


def test_replay_schema_events_複数イベント_順次適用():
    """複数のスキーマイベントを順番に適用できる"""
    events = [
        {
            "event_type": "schema_change",
            "timestamp": "2024-01-01T00:00:00Z",
            "change": {"type": "create_table", "table": "users", "fields": {}}
        },
        {
            "event_type": "schema_change",
            "timestamp": "2024-01-01T01:00:00Z",
            "change": {
                "type": "add_field",
                "table": "users",
                "field": "id",
                "data_type": "INT64"
            }
        }
    ]
    
    schema = replay_schema_events(events)
    assert "users" in schema
    assert "id" in schema["users"]
    assert schema["users"]["id"] == "INT64"


def test_apply_data_with_schema_デフォルト値_自動補完():
    """スキーマに基づいてデータにデフォルト値を適用できる"""
    schema = {
        "users": {
            "fields": {
                "id": {"type": "INT64"},
                "name": {"type": "STRING"},
                "email": {"type": "STRING", "default": ""}
            }
        }
    }
    data_event = {
        "event_type": "create_node",
        "table": "users",
        "data": {"id": 1, "name": "Alice"}  # emailなし
    }
    
    result = apply_data_with_schema(data_event, schema)
    assert result["id"] == 1
    assert result["name"] == "Alice"
    assert result["email"] == ""  # デフォルト値が適用される


def test_create_transformation_function_型変換_文字列から整数():
    """型変換関数を作成して適用できる"""
    transform = create_transformation_function(
        from_type="STRING",
        to_type="INT64",
        converter="parseInt"
    )
    assert transform("123") == 123
    assert transform("456") == 456
    assert transform("abc") is None  # 変換失敗時はNone


def test_generate_sync_checkpoint_イベントリスト_チェックポイント生成():
    """同期用のチェックポイントを生成できる"""
    events = [
        {"event_id": "evt_1", "timestamp": "2024-01-01T00:00:00Z", "event_type": "schema_change"},
        {"event_id": "evt_2", "timestamp": "2024-01-01T01:00:00Z", "event_type": "data_change"}
    ]
    
    checkpoint = generate_sync_checkpoint(events)
    assert checkpoint["event_count"] == 2
    assert checkpoint["last_event_id"] == "evt_2"
    assert checkpoint["hash"] is not None
    assert len(checkpoint["hash"]) == 64  # SHA256


def test_execute_query_at_timestamp_過去時点_スキーマ適用():
    """特定時点のスキーマでクエリを実行できる"""
    events = [
        {
            "event_type": "schema_change",
            "timestamp": "2024-01-01T00:00:00Z",
            "change": {"type": "create_table", "table": "users"}
        },
        {
            "event_type": "schema_change",
            "timestamp": "2024-01-02T00:00:00Z",
            "change": {"type": "add_field", "table": "users", "field": "email"}
        }
    ]
    
    # 2024-01-01時点ではemailフィールドが存在しない
    result = execute_query_at_timestamp(
        query="MATCH (u:users) RETURN u.email",
        timestamp="2024-01-01T12:00:00Z",
        events=events
    )
    assert result["schema_version"] == "2024-01-01"
    assert result["query_translated"] == "MATCH (u:users) RETURN null as email"


def test_serialize_event_イベント_バイト列変換():
    """イベントをシリアライズできる"""
    event = {
        "event_type": "schema_change",
        "timestamp": "2024-01-01T00:00:00Z",
        "change": {"type": "add_field", "field": "test"}
    }
    
    serialized = serialize_event(event)
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0
    
    # デシリアライズして元に戻せる
    deserialized = deserialize_event(serialized)
    assert deserialized["event_type"] == event["event_type"]
    assert deserialized["change"]["field"] == "test"


def test_apply_breaking_change_型変換_データ移行():
    """破壊的変更（型変換）をデータに適用できる"""
    data = {"age": "25", "name": "Bob"}
    change = {
        "type": "change_type",
        "field": "age",
        "from": "STRING",
        "to": "INT64",
        "transformer": "parseInt"
    }
    
    result = apply_breaking_change(data, change)
    assert result["age"] == 25
    assert isinstance(result["age"], int)
    assert result["name"] == "Bob"  # 他のフィールドは変更なし


def test_create_event_index_イベントリスト_インデックス生成():
    """イベントのインデックスを作成できる"""
    events = [
        {"event_id": "evt_1", "timestamp": "2024-01-01T00:00:00Z", "event_type": "schema_change"},
        {"event_id": "evt_2", "timestamp": "2024-01-01T12:00:00Z", "event_type": "data_change"},
        {"event_id": "evt_3", "timestamp": "2024-01-02T00:00:00Z", "event_type": "schema_change"}
    ]
    
    index = create_event_index(events)
    assert "by_date" in index
    assert "by_type" in index
    assert len(index["by_date"]["2024-01-01"]) == 2
    assert len(index["by_date"]["2024-01-02"]) == 1
    assert len(index["by_type"]["schema_change"]) == 2


# REDフェーズ確認用: 単体実行時のテスト
if __name__ == "__main__":
    print("=== TDD RED PHASE - 失敗するテストの実行 ===\n")
    
    tests = [
        test_create_schema_event_基本機能_イベント生成,
        test_apply_add_field_フィールド追加_スキーマ更新,
        test_replay_schema_events_複数イベント_順次適用,
        test_apply_data_with_schema_デフォルト値_自動補完,
        test_create_transformation_function_型変換_文字列から整数,
        test_generate_sync_checkpoint_イベントリスト_チェックポイント生成,
        test_execute_query_at_timestamp_過去時点_スキーマ適用,
        test_serialize_event_イベント_バイト列変換,
        test_apply_breaking_change_型変換_データ移行,
        test_create_event_index_イベントリスト_インデックス生成
    ]
    
    for test in tests:
        print(f"実行中: {test.__name__}")
        try:
            test()
            print("  ✗ 失敗すべきテストが成功しました（実装が既に存在？）")
        except NameError as e:
            print(f"  ✓ RED: {e}")
        except Exception as e:
            print(f"  ✓ RED: {type(e).__name__}: {e}")
        print()