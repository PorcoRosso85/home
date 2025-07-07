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