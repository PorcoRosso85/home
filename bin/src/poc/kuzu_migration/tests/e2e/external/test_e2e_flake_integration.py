#!/usr/bin/env python3
"""
End-to-end tests for lib.mkKuzuMigration function integration.
Tests the external interface of the flake lib function.
"""

import subprocess
import tempfile
import json
import os
import shutil
from pathlib import Path
import pytest


class TestMkKuzuMigrationFunction:
    """Tests for lib.mkKuzuMigration function that generates apps."""
    
    @pytest.fixture
    def temp_test_dir(self):
        """Create a temporary directory for test projects."""
        temp_dir = tempfile.mkdtemp(prefix="kuzu_migration_test_")
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def kuzu_migration_flake_path(self):
        """Get the path to the kuzu_migration flake."""
        # We're in tests/e2e/external/, need to go up 3 levels
        return Path(__file__).parent.parent.parent.parent.absolute()
    
    def create_test_flake(self, test_dir: str, kuzu_migration_path: Path, ddl_path: str = "./ddl") -> Path:
        """Create a test flake that uses lib.mkKuzuMigration."""
        flake_content = f'''{{
  description = "Test flake using lib.mkKuzuMigration";
  
  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-migration.url = "path:{kuzu_migration_path.__fspath__()}";
  }};
  
  outputs = {{ self, nixpkgs, flake-utils, kuzu-migration }}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${{system}};
        
        # Use lib.mkKuzuMigration to generate apps
        migrationApps = kuzu-migration.lib.mkKuzuMigration {{
          inherit pkgs;
          ddlPath = "{ddl_path}";
        }};
      in
      {{
        # Export the generated apps
        apps = migrationApps;
      }});
}}'''
        
        flake_path = Path(test_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        return flake_path
    
    def run_nix_command(self, command: list[str], cwd: str = None) -> subprocess.CompletedProcess:
        """Run a nix command with proper error handling."""
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        return result
    
    def test_mkKuzuMigration_generates_correct_apps(self, temp_test_dir, kuzu_migration_flake_path):
        """Test that lib.mkKuzuMigration generates the expected apps structure."""
        # Create test flake
        self.create_test_flake(temp_test_dir, kuzu_migration_flake_path)
        
        # Run nix flake show to see generated apps
        result = self.run_nix_command(
            ["nix", "flake", "show", "--json"],
            cwd=temp_test_dir
        )
        
        assert result.returncode == 0, f"nix flake show failed: {result.stderr}"
        
        # Parse the output
        flake_info = json.loads(result.stdout)
        
        # Check that apps were generated for the current system
        system_result = subprocess.run(
            ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
            capture_output=True,
            text=True,
            cwd=temp_test_dir
        )
        if system_result.returncode != 0:
            system = "x86_64-linux"
        else:
            system = system_result.stdout.strip()
        
        assert "apps" in flake_info
        assert system in flake_info["apps"]
        
        apps = flake_info["apps"][system]
        
        # Verify all expected apps are present
        expected_apps = ["migrate", "init", "status", "snapshot"]
        for app_name in expected_apps:
            assert app_name in apps, f"Expected app '{app_name}' not found in generated apps"
            assert apps[app_name]["type"] == "app"
    
    def test_migrate_app_has_correct_command(self, temp_test_dir, kuzu_migration_flake_path):
        """Test that the migrate app is created with the proper command."""
        # Create test flake with custom ddl path
        custom_ddl = "./custom/ddl/path"
        self.create_test_flake(temp_test_dir, kuzu_migration_flake_path, ddl_path=custom_ddl)
        
        # Get current system
        system_result = self.run_nix_command(
            ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
            cwd=temp_test_dir
        )
        if system_result.returncode != 0:
            system = "x86_64-linux"
        else:
            system = system_result.stdout.strip()
        
        # Get the migrate app's program path
        result = self.run_nix_command(
            ["nix", "eval", f".#apps.{system}.migrate.program", "--raw"],
            cwd=temp_test_dir
        )
        
        assert result.returncode == 0, f"Failed to get migrate app program: {result.stderr}"
        
        # The program path should contain the expected command
        program_path = result.stdout.strip()
        
        # Verify the program contains the correct command with ddl path
        assert "kuzu-migrate" in program_path
        assert f"--ddl {custom_ddl}" in program_path
        assert "apply" in program_path
    
    def test_ddlPath_parameter_is_correctly_passed(self, temp_test_dir, kuzu_migration_flake_path):
        """Test that ddlPath parameter is correctly passed to all apps."""
        # Test with different ddl paths
        test_paths = ["./ddl", "./migrations/ddl", "/absolute/path/to/ddl"]
        
        for ddl_path in test_paths:
            # Create a new test directory for each test
            test_subdir = Path(temp_test_dir) / f"test_{ddl_path.replace('/', '_')}"
            test_subdir.mkdir(parents=True, exist_ok=True)
            
            self.create_test_flake(str(test_subdir), kuzu_migration_flake_path, ddl_path=ddl_path)
            
            # Get current system
            system_result = self.run_nix_command(
                ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
                cwd=str(test_subdir)
            )
            if system_result.returncode != 0:
                system = "x86_64-linux"
            else:
                system = system_result.stdout.strip()
            
            # Check each app type
            for app_name in ["migrate", "init", "status", "snapshot"]:
                result = self.run_nix_command(
                    ["nix", "eval", f".#apps.{system}.{app_name}.program", "--raw"],
                    cwd=str(test_subdir)
                )
                
                if result.returncode != 0:
                    print(f"Failed to get {app_name} app program: {result.stderr}")
                    continue
                
                program_path = result.stdout.strip()
                
                # Verify ddl path is in the command
                assert f"--ddl {ddl_path}" in program_path, \
                    f"ddlPath '{ddl_path}' not found in {app_name} app program"
    
    def test_default_ddl_path(self, temp_test_dir, kuzu_migration_flake_path):
        """Test that default ddlPath './ddl' is used when not specified."""
        # Create flake without specifying ddlPath
        flake_content = f'''{{
  description = "Test flake with default ddlPath";
  
  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-migration.url = "path:{kuzu_migration_flake_path.__fspath__()}";
  }};
  
  outputs = {{ self, nixpkgs, flake-utils, kuzu-migration }}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${{system}};
        
        # Use lib.mkKuzuMigration without ddlPath (should use default)
        migrationApps = kuzu-migration.lib.mkKuzuMigration {{
          inherit pkgs;
        }};
      in
      {{
        apps = migrationApps;
      }});
}}'''
        
        flake_path = Path(temp_test_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Get current system - use nix eval on the flake itself
        system_result = self.run_nix_command(
            ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
            cwd=temp_test_dir
        )
        
        if system_result.returncode != 0:
            # Fallback to x86_64-linux if we can't detect the system
            system = "x86_64-linux"
        else:
            system = system_result.stdout.strip()
        
        # Get migrate app program path
        result = self.run_nix_command(
            ["nix", "eval", f".#apps.{system}.migrate.program", "--raw"],
            cwd=temp_test_dir
        )
        
        assert result.returncode == 0, f"Failed to get migrate app program: {result.stderr}"
        
        program_path = result.stdout.strip()
        
        # Verify default ddl path is used
        assert "--ddl ./ddl" in program_path
    
    def test_subprocess_verification_with_nix_commands(self, temp_test_dir, kuzu_migration_flake_path):
        """Test using subprocess to run nix commands for verification."""
        # Create test flake
        self.create_test_flake(temp_test_dir, kuzu_migration_flake_path)
        
        # Test that we can run the generated apps (at least check they exist)
        apps_to_test = ["migrate", "init", "status", "snapshot"]
        
        for app_name in apps_to_test:
            # Try to get the program path
            result = self.run_nix_command(
                ["nix", "eval", f".#apps.x86_64-linux.{app_name}.program", "--raw"],
                cwd=temp_test_dir
            )
            
            # On non-x86_64-linux systems, try current system
            if result.returncode != 0:
                system_result = subprocess.run(
                    ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
                    capture_output=True,
                    text=True,
                    cwd=temp_test_dir
                )
                if system_result.returncode != 0:
                    system = "x86_64-linux"
                else:
                    system = system_result.stdout.strip()
                
                result = self.run_nix_command(
                    ["nix", "eval", f".#apps.{system}.{app_name}.program", "--raw"],
                    cwd=temp_test_dir
                )
            
            assert result.returncode == 0, \
                f"Failed to evaluate {app_name} app program: {result.stderr}"
            
            # Verify the program path contains expected elements
            program_path = result.stdout.strip()
            assert "kuzu-migrate" in program_path
            assert app_name in program_path or app_name == "migrate"  # migrate uses "apply" command
    
    def test_all_app_commands_match_expected_structure(self, temp_test_dir, kuzu_migration_flake_path):
        """Test that all generated apps have the correct command structure."""
        # Create test flake
        ddl_path = "./test/ddl"
        self.create_test_flake(temp_test_dir, kuzu_migration_flake_path, ddl_path=ddl_path)
        
        # Expected command patterns for each app
        expected_commands = {
            "migrate": f"kuzu-migrate --ddl {ddl_path} apply",
            "init": f"kuzu-migrate --ddl {ddl_path} init",
            "status": f"kuzu-migrate --ddl {ddl_path} status",
            "snapshot": f"kuzu-migrate --ddl {ddl_path} snapshot"
        }
        
        # Get current system
        system_result = self.run_nix_command(
            ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
            cwd=temp_test_dir
        )
        if system_result.returncode != 0:
            system = "x86_64-linux"
        else:
            system = system_result.stdout.strip()
        
        for app_name, expected_cmd in expected_commands.items():
            # Get the app program path
            result = self.run_nix_command(
                ["nix", "eval", f".#apps.{system}.{app_name}.program", "--raw"],
                cwd=temp_test_dir
            )
            
            assert result.returncode == 0, f"Failed to get {app_name} program: {result.stderr}"
            
            # The program path contains the command
            program_path = result.stdout.strip()
            
            # Verify the expected command components are present
            for cmd_part in expected_cmd.split():
                assert cmd_part in program_path, \
                    f"Expected '{cmd_part}' not found in {app_name} program path"


class TestIntegrationWithExternalFlakes:
    """Test how external flakes can use lib.mkKuzuMigration."""
    
    @pytest.fixture
    def external_project_dir(self):
        """Create a directory for an external project."""
        temp_dir = tempfile.mkdtemp(prefix="external_kuzu_project_")
        
        # Create a basic project structure
        Path(temp_dir, "ddl", "migrations").mkdir(parents=True)
        Path(temp_dir, "ddl", "snapshots").mkdir(parents=True)
        
        # Add a sample migration
        migration_content = """-- Test migration
CREATE NODE TABLE test_table (
    id STRING PRIMARY KEY,
    name STRING
);
"""
        Path(temp_dir, "ddl", "migrations", "001_test.cypher").write_text(migration_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_external_flake_can_use_mkKuzuMigration(self, external_project_dir):
        """Test that an external flake can successfully use lib.mkKuzuMigration."""
        kuzu_migration_path = Path(__file__).parent.parent.parent.parent.absolute()
        
        # Create a flake that references kuzu-migration
        flake_content = f'''{{
  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-migration.url = "path:{kuzu_migration_path.__fspath__()}";
  }};
  
  outputs = {{ self, nixpkgs, flake-utils, kuzu-migration }}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${{system}};
      in
      {{
        apps = kuzu-migration.lib.mkKuzuMigration {{
          inherit pkgs;
          ddlPath = "./ddl";
        }};
      }});
}}'''
        
        Path(external_project_dir, "flake.nix").write_text(flake_content)
        
        # Verify the external project can use the apps
        result = subprocess.run(
            ["nix", "flake", "show", "--json"],
            cwd=external_project_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"External flake failed: {result.stderr}"
        
        flake_info = json.loads(result.stdout)
        system_result = subprocess.run(
            ["nix", "eval", "--impure", "--raw", "--expr", "builtins.currentSystem"],
            capture_output=True,
            text=True,
            cwd=external_project_dir
        )
        if system_result.returncode != 0:
            system = "x86_64-linux"
        else:
            system = system_result.stdout.strip()
        
        # Verify apps are available
        assert "apps" in flake_info
        assert system in flake_info["apps"]
        assert "migrate" in flake_info["apps"][system]
        assert "init" in flake_info["apps"][system]
        assert "status" in flake_info["apps"][system]
        assert "snapshot" in flake_info["apps"][system]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])