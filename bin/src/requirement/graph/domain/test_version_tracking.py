"""
Tests for Version Tracking
"""
import time
from .version_tracking import (
    create_version_id,
    create_location_uri,
    parse_location_uri,
    calculate_requirement_diff
)


def test_create_version_id_generates_unique_id():
    """create_version_id_一意のID_生成される"""
    id1 = create_version_id("req_001")
    time.sleep(0.001)  # 少し待つ
    id2 = create_version_id("req_001")
    
    assert id1 != id2
    assert "req_001" in id1
    assert "req_001" in id2


def test_create_location_uri_generates_standard_uri():
    """create_location_uri_標準URI_生成される"""
    uri = create_location_uri("req_001")
    assert uri == "req://rgl/requirements/req_001"
    
    uri2 = create_location_uri("req_002")
    assert uri2 == "req://rgl/requirements/req_002"


def test_parse_location_uri_extracts_components():
    """parse_location_uri_URI解析_コンポーネント抽出"""
    result = parse_location_uri("req://rgl/requirements/req_001")
    
    assert result["scheme"] == "req"
    assert result["path"] == "/rgl/requirements/req_001"
    assert result["hierarchy"] == ["rgl", "requirements"]
    assert result["id"] == "req_001"


def test_calculate_requirement_diff_detects_changes():
    """calculate_requirement_diff_変更検出_差分を返す"""
    old = {
        "title": "Old Title",
        "description": "Old desc",
        "status": "proposed"
    }
    
    new = {
        "title": "New Title",
        "description": "Old desc",  # 変更なし
        "status": "approved"
    }
    
    diff = calculate_requirement_diff(old, new)
    
    assert len(diff["changed_fields"]) == 2
    assert ("title", "Old Title", "New Title") in diff["changed_fields"]
    assert ("status", "proposed", "approved") in diff["changed_fields"]