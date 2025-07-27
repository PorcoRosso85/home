"""Tests for the ASVS Data Loader Module."""

import pytest
from pathlib import Path
import tempfile
import yaml
from asvs_loader import ASVSLoader


class TestASVSLoader:
    """Test cases for ASVSLoader class."""
    
    @pytest.fixture
    def loader(self):
        """Create an ASVSLoader instance for testing."""
        return ASVSLoader()
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample ASVS data for testing."""
        return {
            "standard": {
                "uri": "ref:standard:owasp:asvs:4.0.3",
                "name": "OWASP ASVS",
                "version": "4.0.3",
                "description": "Test standard",
                "url": "https://example.com"
            },
            "chapters": [
                {
                    "uri": "ref:standard:owasp:asvs:4.0.3:chapter:2",
                    "number": "V2",
                    "name": "Authentication",
                    "description": "Auth chapter",
                    "sections": [
                        {
                            "uri": "ref:standard:owasp:asvs:4.0.3:section:2.1",
                            "number": "V2.1",
                            "name": "Password Security",
                            "description": "Password section",
                            "requirements": [
                                {
                                    "uri": "ref:standard:owasp:asvs:4.0.3:requirement:2.1.1",
                                    "number": "2.1.1",
                                    "description": "Test requirement",
                                    "level1": True,
                                    "level2": True,
                                    "level3": True,
                                    "cwe": 521,
                                    "nist": "5.1.1.2",
                                    "tags": ["password", "authentication"]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def test_loader_initialization(self, loader):
        """Test that loader initializes with correct directories."""
        assert loader.template_dir.name == "templates"
        assert loader.data_dir.name == "data"
        assert loader.env is not None
    
    def test_load_yaml_data(self, loader):
        """Test loading YAML data from file."""
        # Test with the actual sample file
        data = loader.load_yaml_data("asvs_sample.yaml")
        
        assert "standard" in data
        assert data["standard"]["uri"] == "ref:standard:owasp:asvs:4.0.3"
        assert "chapters" in data
        assert len(data["chapters"]) > 0
    
    def test_load_yaml_data_file_not_found(self, loader):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            loader.load_yaml_data("nonexistent.yaml")
    
    def test_generate_cypher(self, loader, sample_data):
        """Test Cypher generation from data."""
        cypher = loader.generate_cypher(sample_data)
        
        # Check that key elements are present
        assert "MERGE (standard:Standard {uri: 'ref:standard:owasp:asvs:4.0.3'})" in cypher
        assert "SET standard.name = 'OWASP ASVS'" in cypher
        assert "MERGE (chapter:Chapter {uri: 'ref:standard:owasp:asvs:4.0.3:chapter:2'})" in cypher
        assert "MERGE (req:Requirement {uri: 'ref:standard:owasp:asvs:4.0.3:requirement:2.1.1'})" in cypher
        assert "CREATE INDEX IF NOT EXISTS" in cypher
    
    def test_generate_cypher_with_tags(self, loader, sample_data):
        """Test that tags are properly rendered in Cypher."""
        cypher = loader.generate_cypher(sample_data)
        
        assert "MERGE (tag:Tag {name: 'password'})" in cypher
        assert "MERGE (tag:Tag {name: 'authentication'})" in cypher
        assert "MERGE (req)-[:TAGGED_WITH]->(tag)" in cypher
    
    def test_generate_cypher_with_optional_fields(self, loader):
        """Test Cypher generation with missing optional fields."""
        data = {
            "standard": {
                "uri": "ref:test",
                "name": "Test",
                "version": "1.0",
                "description": "Test",
                "url": "https://test.com"
            },
            "chapters": [{
                "uri": "ref:test:ch1",
                "number": "1",
                "name": "Chapter",
                "description": "Desc",
                "sections": [{
                    "uri": "ref:test:sec1",
                    "number": "1.1",
                    "name": "Section",
                    "description": "Desc",
                    "requirements": [{
                        "uri": "ref:test:req1",
                        "number": "1.1.1",
                        "description": "Requirement",
                        "level1": True,
                        "level2": False,
                        "level3": False,
                        "cwe": None,
                        "nist": None
                    }]
                }]
            }]
        }
        
        cypher = loader.generate_cypher(data)
        assert "req.cwe = null" in cypher
        assert "req.nist = null" in cypher
    
    def test_load_and_generate(self, loader):
        """Test the combined load and generate functionality."""
        cypher = loader.load_and_generate("asvs_sample.yaml")
        
        # Verify it contains expected content
        assert "OWASP Application Security Verification Standard" in cypher
        assert "2.1.1" in cypher  # The requirement number without V prefix
        assert "Password Security" in cypher
    
    def test_save_cypher(self, loader):
        """Test saving Cypher queries to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            cypher = "MERGE (n:Node {id: 1})"
            
            output_path = loader.save_cypher(cypher, "test.cypher", output_dir)
            
            assert output_path.exists()
            assert output_path.read_text() == cypher
    
    def test_main_function(self, capsys):
        """Test the main function execution."""
        from asvs_loader import main
        
        # Run main function
        main()
        
        # Check output
        captured = capsys.readouterr()
        assert "Generated Cypher queries saved to:" in captured.out
        assert "Generated Cypher" in captured.out


def test_integration_full_workflow():
    """Integration test for the complete workflow."""
    # Initialize loader
    loader = ASVSLoader()
    
    # Load sample data
    data = loader.load_yaml_data("asvs_sample.yaml")
    
    # Generate Cypher
    cypher = loader.generate_cypher(data)
    
    # Verify the generated Cypher contains all expected elements
    expected_elements = [
        # Standard
        "MERGE (standard:Standard {uri: 'ref:standard:owasp:asvs:4.0.3'})",
        "standard.name = 'OWASP Application Security Verification Standard'",
        
        # Chapter
        "MERGE (chapter:Chapter {uri: 'ref:standard:owasp:asvs:4.0.3:chapter:2'})",
        "chapter.name = 'Authentication'",
        
        # Section
        "MERGE (section:Section {uri: 'ref:standard:owasp:asvs:4.0.3:section:2.1'})",
        "section.name = 'Password Security'",
        
        # Requirements
        "MERGE (req:Requirement {uri: 'ref:standard:owasp:asvs:4.0.3:requirement:2.1.1'})",
        "req.description = 'Verify that user set passwords are at least 12 characters in length (after multiple spaces are combined)'",
        "req.level1 = true",
        "req.cwe = 521",
        
        # Relationships
        "MERGE (standard)-[:HAS_CHAPTER]->(chapter)",
        "MERGE (chapter)-[:HAS_SECTION]->(section)",
        "MERGE (section)-[:HAS_REQUIREMENT]->(req)",
        
        # Tags
        "MERGE (tag:Tag {name: 'password'})",
        "MERGE (req)-[:TAGGED_WITH]->(tag)",
        
        # Indexes
        "CREATE INDEX IF NOT EXISTS FOR (s:Standard) ON (s.uri)",
        "CREATE INDEX IF NOT EXISTS FOR (r:Requirement) ON (r.number)"
    ]
    
    for element in expected_elements:
        assert element in cypher, f"Expected element not found: {element}"