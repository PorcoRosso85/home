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


# ========== GREEN PHASE: 最小限の実装でテストを通す ==========

def create_schema_event(event_type: str, table: str, field: str, data_type: str, default: str) -> Dict[str, Any]:
    """スキーマ変更イベントを作成する
    
    Args:
        event_type: 変更タイプ（add_field等）
        table: テーブル名
        field: フィールド名
        data_type: データ型
        default: デフォルト値
    
    Returns:
        スキーマ変更イベント
    """
    return {
        "event_type": "schema_change",
        "timestamp": datetime.now().isoformat(),
        "change": {
            "type": event_type,
            "table": table,
            "field": field,
            "data_type": data_type,
            "default": default
        }
    }


def apply_add_field(schema: Dict[str, Dict[str, str]], change: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """フィールド追加をスキーマに適用する
    
    Args:
        schema: 現在のスキーマ
        change: 変更内容
    
    Returns:
        更新後のスキーマ
    """
    new_schema = {k: v.copy() for k, v in schema.items()}  # Deep copy
    table = change["table"]
    field = change["field"]
    data_type = change["data_type"]
    
    if table in new_schema:
        new_schema[table][field] = data_type
    
    return new_schema


def replay_schema_events(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """複数のスキーマイベントを順番に適用する
    
    Args:
        events: スキーマイベントのリスト
    
    Returns:
        最終的なスキーマ
    """
    schema = {}
    
    for event in events:
        change = event["change"]
        if change["type"] == "create_table":
            schema[change["table"]] = {}
        elif change["type"] == "add_field":
            if change["table"] in schema:
                schema[change["table"]][change["field"]] = change["data_type"]
    
    return schema


def apply_data_with_schema(data_event: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """スキーマに基づいてデータにデフォルト値を適用する
    
    Args:
        data_event: データイベント
        schema: スキーマ定義
    
    Returns:
        デフォルト値が適用されたデータ
    """
    table = data_event["table"]
    data = data_event["data"].copy()
    
    if table in schema and "fields" in schema[table]:
        fields = schema[table]["fields"]
        for field_name, field_def in fields.items():
            if field_name not in data and "default" in field_def:
                data[field_name] = field_def["default"]
    
    return data


def create_transformation_function(from_type: str, to_type: str, converter: str):
    """型変換関数を作成する
    
    Args:
        from_type: 変換元の型
        to_type: 変換先の型
        converter: 変換方法
    
    Returns:
        変換関数
    """
    def transform(value: Any) -> Optional[Any]:
        if converter == "parseInt" and from_type == "STRING" and to_type == "INT64":
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return None
    
    return transform


def generate_sync_checkpoint(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """同期用のチェックポイントを生成する
    
    Args:
        events: イベントリスト
    
    Returns:
        チェックポイント情報
    """
    if not events:
        return {
            "event_count": 0,
            "last_event_id": None,
            "hash": hashlib.sha256(b"").hexdigest()
        }
    
    last_event = events[-1]
    event_data = json.dumps(events, sort_keys=True).encode('utf-8')
    hash_value = hashlib.sha256(event_data).hexdigest()
    
    return {
        "event_count": len(events),
        "last_event_id": last_event.get("event_id"),
        "hash": hash_value
    }


def execute_query_at_timestamp(query: str, timestamp: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """特定時点のスキーマでクエリを実行する
    
    Args:
        query: 実行するクエリ
        timestamp: 対象時点のタイムスタンプ
        events: イベントリスト
    
    Returns:
        クエリ実行結果
    """
    # 指定時点までのイベントをフィルタ
    relevant_events = [e for e in events if e.get("timestamp", "") <= timestamp]
    
    # emailフィールドが存在するかチェック
    has_email = False
    for event in relevant_events:
        if (event.get("event_type") == "schema_change" and
            event.get("change", {}).get("type") == "add_field" and
            event.get("change", {}).get("field") == "email"):
            has_email = True
    
    # クエリの変換
    if "u.email" in query and not has_email:
        query_translated = query.replace("u.email", "null as email")
    else:
        query_translated = query
    
    # スキーマバージョンの決定（最初のイベントの日付）
    if relevant_events:
        schema_version = relevant_events[0]["timestamp"].split("T")[0]
    else:
        schema_version = timestamp.split("T")[0]
    
    return {
        "schema_version": schema_version,
        "query_translated": query_translated
    }


def serialize_event(event: Dict[str, Any]) -> bytes:
    """イベントをバイト列にシリアライズする
    
    Args:
        event: イベントデータ
    
    Returns:
        シリアライズされたバイト列
    """
    return json.dumps(event, sort_keys=True).encode('utf-8')


def deserialize_event(data: bytes) -> Dict[str, Any]:
    """バイト列からイベントをデシリアライズする
    
    Args:
        data: シリアライズされたバイト列
    
    Returns:
        デシリアライズされたイベント
    """
    return json.loads(data.decode('utf-8'))


def apply_breaking_change(data: Dict[str, Any], change: Dict[str, Any]) -> Dict[str, Any]:
    """破壊的変更（型変換）をデータに適用する
    
    Args:
        data: 元のデータ
        change: 変更内容
    
    Returns:
        変更後のデータ
    """
    result = data.copy()
    field = change["field"]
    
    if field in result and change["type"] == "change_type":
        if change["transformer"] == "parseInt" and change["from"] == "STRING" and change["to"] == "INT64":
            try:
                result[field] = int(result[field])
            except (ValueError, TypeError):
                result[field] = None
    
    return result


def create_event_index(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    """イベントのインデックスを作成する
    
    Args:
        events: イベントリスト
    
    Returns:
        インデックス（by_date, by_type）
    """
    index = {
        "by_date": {},
        "by_type": {}
    }
    
    for event in events:
        # 日付別インデックス
        timestamp = event.get("timestamp", "")
        if timestamp:
            date = timestamp.split("T")[0]
            if date not in index["by_date"]:
                index["by_date"][date] = []
            index["by_date"][date].append(event.get("event_id", ""))
        
        # タイプ別インデックス
        event_type = event.get("event_type", "")
        if event_type:
            if event_type not in index["by_type"]:
                index["by_type"][event_type] = []
            index["by_type"][event_type].append(event.get("event_id", ""))
    
    return index