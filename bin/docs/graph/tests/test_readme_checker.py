"""Test README checker functionality"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from flake_graph.readme_checker import check_missing_readmes, generate_missing_readme_report


class TestReadmeChecker:
    """Test suite for README missing detection"""

    def test_detect_missing_readme_single_flake(self, tmp_path):
        """Test detection of single flake.nix without README.md"""
        # Arrange
        flake_dir = tmp_path / "project1"
        flake_dir.mkdir()
        (flake_dir / "flake.nix").write_text("{ inputs = {}; }")
        
        # Act
        missing = check_missing_readmes(tmp_path)
        
        # Assert
        assert len(missing) == 1
        assert flake_dir in missing
        
    def test_no_missing_readme_when_both_exist(self, tmp_path):
        """Test no detection when both flake.nix and README.md exist"""
        # Arrange
        flake_dir = tmp_path / "project2"
        flake_dir.mkdir()
        (flake_dir / "flake.nix").write_text("{ inputs = {}; }")
        (flake_dir / "README.md").write_text("# Project 2")
        
        # Act
        missing = check_missing_readmes(tmp_path)
        
        # Assert
        assert len(missing) == 0
        
    def test_multiple_missing_readmes(self, tmp_path):
        """Test detection of multiple flakes without READMEs"""
        # Arrange
        for i in range(3):
            flake_dir = tmp_path / f"project{i}"
            flake_dir.mkdir()
            (flake_dir / "flake.nix").write_text("{ inputs = {}; }")
            
        # Add one with README
        with_readme = tmp_path / "project_with_readme"
        with_readme.mkdir()
        (with_readme / "flake.nix").write_text("{ inputs = {}; }")
        (with_readme / "README.md").write_text("# With README")
        
        # Act
        missing = check_missing_readmes(tmp_path)
        
        # Assert
        assert len(missing) == 3
        # Check all project directories are in the missing list
        missing_names = [path.name for path in missing]
        for i in range(3):
            assert f"project{i}" in missing_names
        
    def test_nested_flakes_detection(self, tmp_path):
        """Test detection in nested directory structures"""
        # Arrange
        parent = tmp_path / "parent"
        parent.mkdir()
        (parent / "flake.nix").write_text("{ inputs = {}; }")
        
        child = parent / "child"
        child.mkdir()
        (child / "flake.nix").write_text("{ inputs = {}; }")
        (child / "README.md").write_text("# Child README")
        
        # Act
        missing = check_missing_readmes(tmp_path)
        
        # Assert
        assert len(missing) == 1
        assert parent in missing
        assert child not in missing
        
    def test_report_format(self, tmp_path):
        """Test the report format for missing READMEs"""
        # Arrange
        projects = ["api", "frontend", "backend"]
        for proj in projects:
            proj_dir = tmp_path / proj
            proj_dir.mkdir()
            (proj_dir / "flake.nix").write_text("{ inputs = {}; }")
            
        # Act
        missing = check_missing_readmes(tmp_path)
        
        # Assert
        assert len(missing) == 3
        # Results should be sorted for consistent reporting
        missing_sorted = sorted(missing, key=str)
        missing_names = [path.name for path in missing_sorted]
        assert missing_names == ["api", "backend", "frontend"]
        
    def test_empty_directory(self, tmp_path):
        """Test behavior with empty directory"""
        # Act
        missing = check_missing_readmes(tmp_path)
        
        # Assert
        assert len(missing) == 0
        
    def test_ignore_non_flake_directories(self, tmp_path):
        """Test that directories without flake.nix are ignored"""
        # Arrange
        no_flake = tmp_path / "no_flake"
        no_flake.mkdir()
        (no_flake / "README.md").write_text("# README without flake")
        
        # Act
        missing = check_missing_readmes(tmp_path)
        
        # Assert
        assert len(missing) == 0


class TestMissingReadmeReport:
    """Test suite for missing README report generation"""
    
    def test_report_no_missing_readmes(self, tmp_path):
        """Test report when all flakes have READMEs"""
        # Arrange
        flake_dir = tmp_path / "project"
        flake_dir.mkdir()
        (flake_dir / "flake.nix").write_text("{ inputs = {}; }")
        (flake_dir / "README.md").write_text("# Project")
        
        # Act
        report = generate_missing_readme_report(tmp_path)
        
        # Assert
        assert "🎉 All flake projects have README documentation!" in report
        
    def test_report_with_priority_grouping(self, tmp_path):
        """Test report groups missing READMEs by priority"""
        # Arrange - Create different priority directories
        # High priority: src directories
        src_dir = tmp_path / "src" / "core"
        src_dir.mkdir(parents=True)
        (src_dir / "flake.nix").write_text("{ inputs = {}; }")
        
        # Medium priority: test directories
        test_dir = tmp_path / "tests" / "integration"
        test_dir.mkdir(parents=True)
        (test_dir / "flake.nix").write_text("{ inputs = {}; }")
        
        # Low priority: other directories
        misc_dir = tmp_path / "tools" / "helper"
        misc_dir.mkdir(parents=True)
        (misc_dir / "flake.nix").write_text("{ inputs = {}; }")
        
        # Act
        report = generate_missing_readme_report(tmp_path)
        
        # Assert
        assert "📋 Missing README Alert Report" in report
        assert "📊 Summary: 3 flake(s) missing README documentation" in report
        assert "🔴 HIGH Priority (src directories)" in report
        assert "🟡 MEDIUM Priority (test/example/poc directories)" in report
        assert "🟢 LOW Priority (other directories)" in report
        assert "src/core" in report
        assert "tests/integration" in report
        assert "tools/helper" in report
        
    def test_report_format_readability(self, tmp_path):
        """Test report format is human-readable with proper structure"""
        # Arrange
        projects = [
            "src/api",
            "src/frontend",
            "poc/experiment",
            "lib/utils"
        ]
        
        for proj in projects:
            proj_path = tmp_path / proj
            proj_path.mkdir(parents=True)
            (proj_path / "flake.nix").write_text("{ inputs = {}; }")
            
        # Act
        report = generate_missing_readme_report(tmp_path)
        lines = report.split("\n")
        
        # Assert structure
        assert lines[0] == "=" * 60
        assert "📋 Missing README Alert Report" in lines[1]
        assert "=" * 60 in lines[2]
        assert "Summary: 4 flake(s) missing" in report
        assert "• src/api" in report
        assert "• src/frontend" in report
        assert "• poc/experiment" in report
        assert "• lib/utils" in report
        assert "💡 Recommendation: Start with HIGH priority directories" in report
        
    def test_report_only_shows_existing_priorities(self, tmp_path):
        """Test report only shows priority groups that have missing READMEs"""
        # Arrange - Only create high priority missing READMEs
        src_dirs = ["src/module1", "src/module2"]
        for dir_path in src_dirs:
            full_path = tmp_path / dir_path
            full_path.mkdir(parents=True)
            (full_path / "flake.nix").write_text("{ inputs = {}; }")
            
        # Act
        report = generate_missing_readme_report(tmp_path)
        
        # Assert
        assert "🔴 HIGH Priority" in report
        assert "🟡 MEDIUM Priority" not in report
        assert "🟢 LOW Priority" not in report
        
    def test_report_relative_paths(self, tmp_path):
        """Test report shows relative paths from root"""
        # Arrange
        deep_path = tmp_path / "a" / "b" / "c" / "project"
        deep_path.mkdir(parents=True)
        (deep_path / "flake.nix").write_text("{ inputs = {}; }")
        
        # Act  
        report = generate_missing_readme_report(tmp_path)
        
        # Assert
        assert "• a/b/c/project" in report
        assert str(tmp_path) not in report  # Should not contain absolute paths
        
    def test_report_sorted_within_priority(self, tmp_path):
        """Test paths are sorted within each priority group"""
        # Arrange - Create multiple src directories in non-alphabetical order
        src_projects = ["src/zebra", "src/alpha", "src/beta"]
        for proj in src_projects:
            proj_path = tmp_path / proj
            proj_path.mkdir(parents=True)
            (proj_path / "flake.nix").write_text("{ inputs = {}; }")
            
        # Act
        report = generate_missing_readme_report(tmp_path)
        lines = report.split("\n")
        
        # Find HIGH priority section
        high_idx = next(i for i, line in enumerate(lines) if "HIGH Priority" in line)
        
        # Extract paths after HIGH priority section
        paths = []
        for line in lines[high_idx+2:]:  # Skip header and separator
            if line.strip().startswith("•"):
                paths.append(line.strip())
            elif line.strip() == "":
                break
                
        # Assert they appear in alphabetical order
        assert "• src/alpha" in paths[0]
        assert "• src/beta" in paths[1]  
        assert "• src/zebra" in paths[2]