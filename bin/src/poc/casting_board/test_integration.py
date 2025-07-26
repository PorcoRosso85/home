"""
Integration tests for casting board POC.

Tests the complete flow from domain layer through infrastructure.
"""
import pytest
from datetime import datetime
from .domain import create_resource, add_capability
from .infrastructure import create_in_memory_database, ResourceRepository


class TestResourceIntegration:
    """Integration tests for Resource management with KuzuDB."""
    
    def test_complete_resource_lifecycle(self):
        """リソースの作成から検索まで完全なライフサイクルをテスト"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        # Act: Create and save a human resource
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        resource = add_capability(resource, "PYTHON_SKILL", 5)
        resource = add_capability(resource, "LEADERSHIP", 4)
        
        save_result = repo.save(resource)
        
        # Assert: Save successful
        assert "type" not in save_result
        
        # Act: Find the resource
        found = repo.find_by_id("res-001")
        
        # Assert: Resource found with all data
        assert found is not None
        assert found["id"] == "res-001"
        assert found["name"] == "田中太郎"
        assert found["resource_type"] == "HUMAN"
        assert len(found["capabilities"]) == 2
        
        # Check capabilities
        capability_names = {cap["name"] for cap in found["capabilities"]}
        assert "PYTHON_SKILL" in capability_names
        assert "LEADERSHIP" in capability_names
    
    def test_capability_based_search_scenario(self):
        """実際のキャスティングシナリオでの能力検索をテスト"""
        # Arrange: Setup a casting board scenario
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        # Create actors with different skills
        actor1 = create_resource("actor-001", "山田花子", "HUMAN")
        actor1 = add_capability(actor1, "ACTING", 5)
        actor1 = add_capability(actor1, "SINGING", 3)
        repo.save(actor1)
        
        actor2 = create_resource("actor-002", "鈴木一郎", "HUMAN")
        actor2 = add_capability(actor2, "ACTING", 4)
        actor2 = add_capability(actor2, "DANCING", 5)
        repo.save(actor2)
        
        actor3 = create_resource("actor-003", "佐藤次郎", "HUMAN")
        actor3 = add_capability(actor3, "ACTING", 3)
        actor3 = add_capability(actor3, "SINGING", 5)
        repo.save(actor3)
        
        # Create equipment resources
        camera = create_resource("equip-001", "カメラA", "EQUIPMENT")
        camera = add_capability(camera, "RESOLUTION_4K", 1)
        repo.save(camera)
        
        # Act: Find actors with high acting skill
        skilled_actors = repo.find_by_capability("ACTING", minimum_level=4)
        
        # Assert: Found the right actors
        assert len(skilled_actors) == 2
        actor_ids = {actor["id"] for actor in skilled_actors}
        assert "actor-001" in actor_ids
        assert "actor-002" in actor_ids
        assert "actor-003" not in actor_ids  # Acting level is only 3
    
    def test_resource_update_scenario(self):
        """リソースのスキルアップシナリオをテスト"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        # Create a junior developer
        developer = create_resource("dev-001", "新人太郎", "HUMAN")
        developer = add_capability(developer, "PYTHON_SKILL", 2)
        repo.save(developer)
        
        # Act: Developer improves skills
        developer = add_capability(developer, "PYTHON_SKILL", 4)  # Level up!
        developer = add_capability(developer, "JAVA_SKILL", 3)    # New skill
        repo.save(developer)
        
        # Assert: Skills are updated
        updated = repo.find_by_id("dev-001")
        assert len(updated["capabilities"]) == 2
        
        python_skill = next(
            cap for cap in updated["capabilities"] 
            if cap["name"] == "PYTHON_SKILL"
        )
        assert python_skill["level"] == 4  # Updated from 2 to 4
        
        java_skill = next(
            cap for cap in updated["capabilities"] 
            if cap["name"] == "JAVA_SKILL"
        )
        assert java_skill["level"] == 3  # New skill added
    
    def test_mixed_resource_types(self):
        """異なるリソースタイプの混在シナリオをテスト"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        # Create different types of resources
        human = create_resource("res-h001", "スタッフA", "HUMAN")
        human = add_capability(human, "CAMERA_OPERATION", 4)
        repo.save(human)
        
        equipment = create_resource("res-e001", "カメラ機材", "EQUIPMENT")
        equipment = add_capability(equipment, "RESOLUTION_8K", 1)
        repo.save(equipment)
        
        vehicle = create_resource("res-v001", "撮影車", "VEHICLE")
        vehicle = add_capability(vehicle, "CARGO_CAPACITY", 1000)
        repo.save(vehicle)
        
        location = create_resource("res-l001", "スタジオA", "LOCATION")
        location = add_capability(location, "FLOOR_SPACE", 200)
        repo.save(location)
        
        # Act & Assert: Each resource type is saved and retrieved correctly
        assert repo.find_by_id("res-h001")["resource_type"] == "HUMAN"
        assert repo.find_by_id("res-e001")["resource_type"] == "EQUIPMENT"
        assert repo.find_by_id("res-v001")["resource_type"] == "VEHICLE"
        assert repo.find_by_id("res-l001")["resource_type"] == "LOCATION"