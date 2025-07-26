"""
Resource entity tests following TDD RED phase.

These tests express business value as executable specifications,
focusing on behavior rather than implementation details.
"""
import pytest
from datetime import datetime
from .domain import (
    create_resource,
    add_capability,
    has_capability,
    is_available,
    ResourceDict,
    CapabilityDict,
    TimeSlotDict,
    ErrorDict,
)


class TestResourceCreation:
    """Tests for Resource entity creation with type validation."""
    
    def test_create_human_resource(self):
        """リソースタイプがHUMANのリソースを作成できる"""
        # Arrange
        resource_id = "res-001"
        name = "田中太郎"
        resource_type = "HUMAN"
        
        # Act
        result = create_resource(resource_id, name, resource_type)
        
        # Assert
        assert "type" not in result  # Success case
        assert result["id"] == "res-001"
        assert result["name"] == "田中太郎"
        assert result["resource_type"] == "HUMAN"
        assert result["capabilities"] == []
    
    def test_create_equipment_resource(self):
        """リソースタイプがEQUIPMENTのリソースを作成できる"""
        # Arrange
        resource_id = "res-002"
        name = "カメラA"
        resource_type = "EQUIPMENT"
        
        # Act
        result = create_resource(resource_id, name, resource_type)
        
        # Assert
        assert "type" not in result  # Success case
        assert result["resource_type"] == "EQUIPMENT"
    
    def test_create_resource_with_invalid_type(self):
        """無効なリソースタイプでの作成はエラーを返す"""
        # Arrange
        resource_id = "res-003"
        name = "Invalid Resource"
        resource_type = "INVALID_TYPE"
        
        # Act
        result = create_resource(resource_id, name, resource_type)
        
        # Assert
        assert result["type"] == "ValidationError"
        assert "Invalid resource type" in result["message"]
    
    def test_create_resource_without_required_fields(self):
        """必須フィールドが欠けている場合はエラーを返す"""
        # Arrange
        resource_id = ""
        name = "Incomplete Resource"
        resource_type = "HUMAN"
        
        # Act
        result = create_resource(resource_id, name, resource_type)
        
        # Assert
        assert result["type"] == "ValidationError"
        assert "required" in result["message"].lower()


class TestCapabilityManagement:
    """Tests for managing Resource capabilities."""
    
    def test_add_capability_to_resource(self):
        """リソースに能力を追加できる"""
        # Arrange
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        
        # Act
        result = add_capability(resource, "PYTHON_SKILL", 5)
        
        # Assert
        assert "type" not in result  # Success case
        assert len(result["capabilities"]) == 1
        assert result["capabilities"][0]["name"] == "PYTHON_SKILL"
        assert result["capabilities"][0]["level"] == 5
    
    def test_add_multiple_capabilities(self):
        """複数の能力を持つリソースを管理できる"""
        # Arrange
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        
        # Act
        resource = add_capability(resource, "PYTHON_SKILL", 5)
        resource = add_capability(resource, "JAVA_SKILL", 3)
        resource = add_capability(resource, "LEADERSHIP", 4)
        
        # Assert
        assert len(resource["capabilities"]) == 3
        capability_names = [cap["name"] for cap in resource["capabilities"]]
        assert "PYTHON_SKILL" in capability_names
        assert "JAVA_SKILL" in capability_names
        assert "LEADERSHIP" in capability_names
    
    def test_query_resource_capabilities(self):
        """リソースが特定の能力を持っているか確認できる"""
        # Arrange
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        resource = add_capability(resource, "PYTHON_SKILL", 5)
        resource = add_capability(resource, "JAVA_SKILL", 3)
        
        # Act & Assert
        # Check capability with sufficient level
        assert has_capability(resource, "PYTHON_SKILL", minimum_level=3) is True
        assert has_capability(resource, "PYTHON_SKILL", minimum_level=6) is False
        
        # Check non-existent capability
        assert has_capability(resource, "RUBY_SKILL", minimum_level=1) is False
        
        # Check capability without minimum level requirement
        assert has_capability(resource, "JAVA_SKILL") is True
    
    def test_add_duplicate_capability_updates_level(self):
        """同じ名前の能力を追加するとレベルが更新される"""
        # Arrange
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        resource = add_capability(resource, "PYTHON_SKILL", 3)
        
        # Act
        result = add_capability(resource, "PYTHON_SKILL", 5)
        
        # Assert
        assert len(result["capabilities"]) == 1  # Still only one capability
        assert result["capabilities"][0]["level"] == 5  # Updated to new level


class TestAvailabilityChecking:
    """Tests for checking Resource availability in time slots."""
    
    def test_check_resource_availability_in_time_slot(self):
        """指定された時間枠でリソースが利用可能か確認できる"""
        # Arrange
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        # Add availability slots
        resource["availability"] = [
            {
                "start_time": datetime(2024, 1, 15, 9, 0, 0),
                "end_time": datetime(2024, 1, 15, 17, 0, 0)
            },
            {
                "start_time": datetime(2024, 1, 16, 9, 0, 0),
                "end_time": datetime(2024, 1, 16, 17, 0, 0)
            }
        ]
        
        # Act
        # Check within available time
        time_slot_1 = TimeSlotDict(
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 12, 0, 0)
        )
        available_1 = is_available(resource, time_slot_1)
        
        # Check outside available time
        time_slot_2 = TimeSlotDict(
            start_time=datetime(2024, 1, 15, 8, 0, 0),
            end_time=datetime(2024, 1, 15, 10, 0, 0)
        )
        available_2 = is_available(resource, time_slot_2)
        
        # Check spanning multiple days
        time_slot_3 = TimeSlotDict(
            start_time=datetime(2024, 1, 15, 16, 0, 0),
            end_time=datetime(2024, 1, 16, 10, 0, 0)
        )
        available_3 = is_available(resource, time_slot_3)
        
        # Assert
        assert available_1 is True  # Fully within available slot
        assert available_2 is False  # Starts before available time
        assert available_3 is False  # Spans across slots
    
    def test_resource_without_availability_is_never_available(self):
        """可用性情報がないリソースは常に利用不可"""
        # Arrange
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        # No availability added
        
        # Act
        time_slot = TimeSlotDict(
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 12, 0, 0)
        )
        result = is_available(resource, time_slot)
        
        # Assert
        assert result is False