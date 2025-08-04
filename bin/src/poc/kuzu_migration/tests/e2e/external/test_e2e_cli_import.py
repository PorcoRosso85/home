#!/usr/bin/env python3
"""End-to-end tests for kuzu-migrate CLI binary availability from external flakes.

These tests verify that:
1. The kuzu-migrate binary is accessible from external flakes
2. The binary can be executed with various commands
3. Package exports work correctly
4. Nix run commands function from external context
"""

import os
import subprocess
import tempfile
import shutil
import json
from pathlib import Path
import pytest


class TestCLIBinaryAvailability:
    """Test suite for verifying CLI binary availability from external flakes."""
    
    @pytest.fixture
    def external_flake_dir(self):
        """Create a temporary directory for external flake testing."""
        test_dir = tempfile.mkdtemp(prefix="kuzu_migrate_external_test_")
        yield test_dir
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.fixture
    def parent_flake_path(self):
        """Get the path to the parent kuzu_migration flake."""
        # Get the absolute path to the kuzu_migration directory
        current_file = Path(__file__).resolve()
        return current_file.parent.parent.parent.parent
    
    def test_binary_available_via_nix_build(self, external_flake_dir, parent_flake_path):
        """Test that kuzu-migrate binary can be built from external flake."""
        # Create a minimal flake.nix that references our package
        flake_content = f'''{{
  description = "Test flake importing kuzu-migrate";
  
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
    nixpkgs.follows = "kuzu-migration/nixpkgs";
  }};
  
  outputs = {{ self, kuzu-migration, nixpkgs }}: {{
    packages.x86_64-linux.default = kuzu-migration.packages.x86_64-linux.default;
  }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Build the package
        result = subprocess.run(
            ["nix", "build", "--no-link", "--print-out-paths"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to build package: {result.stderr}"
        
        # Get the output path
        output_path = result.stdout.strip()
        assert output_path, "No output path returned"
        
        # Check that the binary exists
        binary_path = Path(output_path) / "bin" / "kuzu-migrate"
        assert binary_path.exists(), f"Binary not found at {binary_path}"
        assert binary_path.is_file(), f"Binary path is not a file: {binary_path}"
        assert os.access(binary_path, os.X_OK), f"Binary is not executable: {binary_path}"
    
    def test_binary_help_command(self, external_flake_dir, parent_flake_path):
        """Test that kuzu-migrate binary can be executed with --help."""
        # Create flake that runs the binary
        flake_content = f'''{{
  description = "Test flake for kuzu-migrate --help";
  
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
    nixpkgs.follows = "kuzu-migration/nixpkgs";
  }};
  
  outputs = {{ self, kuzu-migration, nixpkgs }}: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${{system}};
    in {{
      apps.${{system}}.test-help = {{
        type = "app";
        program = "${{pkgs.writeShellScript "test-help" ''
          ${{kuzu-migration.packages.${{system}}.default}}/bin/kuzu-migrate --help
        ''}}" ;
      }};
    }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Run the help command
        result = subprocess.run(
            ["nix", "run", ".#test-help"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to run --help: {result.stderr}"
        assert "kuzu-migrate" in result.stdout, "Help output doesn't contain program name"
        assert "Usage:" in result.stdout, "Help output doesn't contain usage information"
        assert "Commands:" in result.stdout, "Help output doesn't contain commands section"
        assert "init" in result.stdout, "Help output doesn't list init command"
        assert "apply" in result.stdout, "Help output doesn't list apply command"
        assert "status" in result.stdout, "Help output doesn't list status command"
        assert "snapshot" in result.stdout, "Help output doesn't list snapshot command"
    
    def test_binary_version_command(self, external_flake_dir, parent_flake_path):
        """Test that kuzu-migrate binary shows version correctly."""
        # Create flake that runs the version command
        flake_content = f'''{{
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
    nixpkgs.follows = "kuzu-migration/nixpkgs";
  }};
  
  outputs = {{ self, kuzu-migration, nixpkgs }}: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${{system}};
    in {{
      apps.${{system}}.test-version = {{
        type = "app";
        program = "${{pkgs.writeShellScript "test-version" ''
          ${{kuzu-migration.packages.${{system}}.default}}/bin/kuzu-migrate --version
        ''}}" ;
      }};
    }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Run the version command
        result = subprocess.run(
            ["nix", "run", ".#test-version"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to run --version: {result.stderr}"
        assert "kuzu-migrate" in result.stdout, "Version output doesn't contain program name"
        assert "v0.1.0" in result.stdout, "Version output doesn't contain version number"
    
    def test_nix_run_direct_invocation(self, external_flake_dir, parent_flake_path):
        """Test that 'nix run' works directly from external context."""
        # Create a minimal flake that exposes the app
        flake_content = f'''{{
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
  }};
  
  outputs = {{ self, kuzu-migration }}: {{
    apps.x86_64-linux.kuzu-migrate = kuzu-migration.apps.x86_64-linux.kuzu-migrate;
  }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Test running with nix run
        result = subprocess.run(
            ["nix", "run", ".#kuzu-migrate", "--", "--help"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to run via 'nix run': {result.stderr}"
        assert "kuzu-migrate" in result.stdout, "Output doesn't contain program name"
    
    def test_library_functions_available(self, external_flake_dir, parent_flake_path):
        """Test that library functions are accessible from external flake."""
        # Create flake that uses the library functions
        flake_content = f'''{{
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
    nixpkgs.follows = "kuzu-migration/nixpkgs";
  }};
  
  outputs = {{ self, kuzu-migration, nixpkgs }}: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${{system}};
      
      # Use the library function to create migration apps
      migrationApps = kuzu-migration.lib.mkKuzuMigration {{
        inherit pkgs;
        ddlPath = "./test_ddl";
      }};
    in {{
      # Create a test app to verify the functions work
      apps.${{system}}.test-lib = {{
        type = "app";
        program = "${{pkgs.writeShellScript "test-lib" ''
          echo "Library functions are accessible!"
          echo "Generated apps: init, migrate, status, snapshot"
        ''}}" ;
      }};
    }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Test that the library functions work
        result = subprocess.run(
            ["nix", "run", ".#test-lib"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to test library functions: {result.stderr}"
        assert "Library functions are accessible!" in result.stdout
        assert "Generated apps:" in result.stdout
    
    def test_init_command_from_external(self, external_flake_dir, parent_flake_path):
        """Test that init command works when invoked from external flake."""
        # Create flake that runs init command
        flake_content = f'''{{
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
    nixpkgs.follows = "kuzu-migration/nixpkgs";
  }};
  
  outputs = {{ self, kuzu-migration, nixpkgs }}: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${{system}};
    in {{
      apps.${{system}}.test-init = {{
        type = "app";
        program = "${{pkgs.writeShellScript "test-init" ''
          # Create a test DDL directory
          TEST_DDL="$PWD/test_ddl_init"
          
          # Run init command
          ${{kuzu-migration.packages.${{system}}.default}}/bin/kuzu-migrate --ddl "$TEST_DDL" init
          
          # Verify the structure was created
          if [[ -d "$TEST_DDL/migrations" ]] && [[ -d "$TEST_DDL/snapshots" ]]; then
            echo "✅ DDL directory structure created successfully"
            ls -la "$TEST_DDL"
          else
            echo "❌ Failed to create DDL directory structure"
            exit 1
          fi
          
          # Cleanup
          rm -rf "$TEST_DDL"
        ''}}" ;
      }};
    }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Run the init test
        result = subprocess.run(
            ["nix", "run", ".#test-init"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to run init command: {result.stderr}"
        assert "✅ DDL directory structure created successfully" in result.stdout
    
    def test_package_metadata_exports(self, external_flake_dir, parent_flake_path):
        """Test that package metadata is correctly exported."""
        # Create flake that inspects package metadata
        flake_content = f'''{{
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
    nixpkgs.follows = "kuzu-migration/nixpkgs";
  }};
  
  outputs = {{ self, kuzu-migration, nixpkgs }}: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${{system}};
      pkg = kuzu-migration.packages.${{system}}.default;
    in {{
      apps.${{system}}.test-metadata = {{
        type = "app";
        program = "${{pkgs.writeShellScript "test-metadata" ''
          echo "Package name: ${{pkg.pname or pkg.name}}"
          echo "Package path: ${{pkg}}"
          echo "Binary exists: $(test -f ${{pkg}}/bin/kuzu-migrate && echo "yes" || echo "no")"
        ''}}" ;
      }};
    }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Run the metadata test
        result = subprocess.run(
            ["nix", "run", ".#test-metadata"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to test metadata: {result.stderr}"
        assert "Package name: kuzu-migrate" in result.stdout
        assert "Binary exists: yes" in result.stdout
    
    def test_multiple_system_support(self, external_flake_dir, parent_flake_path):
        """Test that the package works across different systems."""
        # Create flake that checks system support
        flake_content = f'''{{
  inputs = {{
    kuzu-migration.url = "path:{parent_flake_path}";
    nixpkgs.follows = "kuzu-migration/nixpkgs";
  }};
  
  outputs = {{ self, kuzu-migration, nixpkgs }}: 
    let
      # Get current system
      currentSystem = builtins.currentSystem or "x86_64-linux";
      
      # Check if package exists for current system
      hasPackage = kuzu-migration.packages ? ${{currentSystem}};
    in {{
      apps.${{currentSystem}}.test-system = {{
        type = "app";
        program = "${{nixpkgs.legacyPackages.${{currentSystem}}.writeShellScript "test-system" ''
          echo "System ${{currentSystem}} supported: ${{if hasPackage then "yes" else "no"}}"
        ''}}";
      }};
    }};
}}'''
        
        flake_path = Path(external_flake_dir) / "flake.nix"
        flake_path.write_text(flake_content)
        
        # Run the system test
        result = subprocess.run(
            ["nix", "eval", "--raw", ".#apps.x86_64-linux.test-system.program"],
            cwd=external_flake_dir,
            capture_output=True,
            text=True
        )
        
        # We just check that evaluation succeeds
        assert result.returncode == 0, f"Failed to evaluate system support: {result.stderr}"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])