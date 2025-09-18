"""E2E tests for kuzu-migrate usage display."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestE2EUsageDisplay:
    """Test the kuzu-migrate usage display end-to-end."""

    @pytest.fixture
    def kuzu_migrate_path(self):
        """Path to the kuzu-migrate CLI script."""
        # Get the path relative to this test file
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent.parent  # Navigate up to project root
        return str(project_root / "src" / "kuzu-migrate.sh")

    def run_command(self, args, cwd=None, env=None):
        """Run a command and return the result."""
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env
        )
        return result

    def test_no_args_shows_usage_display(self, kuzu_migrate_path):
        """Test that running kuzu-migrate with no args shows usage display."""
        # Execute
        result = self.run_command([kuzu_migrate_path])
        
        # Verify exit code is non-zero (error)
        assert result.returncode != 0
        
        # Verify usage is shown in stderr (error output)
        assert "kuzu-migrate" in result.stderr
        assert "USAGE:" in result.stderr
        assert "COMMANDS:" in result.stderr
        assert "OPTIONS:" in result.stderr
        
        # Verify getting started section
        assert "GETTING STARTED:" in result.stderr

    def test_help_flag_shows_full_usage(self, kuzu_migrate_path):
        """Test that --help flag shows complete usage information."""
        # Execute
        result = self.run_command([kuzu_migrate_path, "--help"])
        
        # Verify successful exit
        assert result.returncode == 0
        
        # Verify usage header
        assert "kuzu-migrate" in result.stdout
        assert "Manage your KuzuDB schema migrations" in result.stdout
        
        # Verify command list with descriptions
        commands = {
            "init": "Create the DDL directory structure",
            "apply": "Execute pending migrations",
            "status": "Check which migrations",
            "snapshot": "Export the current database",
            "rollback": "Restore database from"
        }
        
        for cmd, desc in commands.items():
            assert cmd in result.stdout
            # Check that description contains expected keywords
            assert desc in result.stdout or desc.lower() in result.stdout.lower()
        
        # Verify getting started section
        assert "GETTING STARTED:" in result.stdout
        assert "kuzu-migrate init" in result.stdout
        assert "kuzu-migrate apply" in result.stdout
        assert "kuzu-migrate status" in result.stdout
        
        # Verify options section
        assert "OPTIONS:" in result.stdout
        assert "--ddl DIR" in result.stdout
        assert "--db PATH" in result.stdout
        assert "--help" in result.stdout
        assert "--version" in result.stdout

    def test_help_format_is_concise_and_organized(self, kuzu_migrate_path):
        """Test that help output is well-formatted and concise."""
        # Execute
        result = self.run_command([kuzu_migrate_path, "--help"])
        
        # Verify the output is reasonably sized (not too verbose)
        lines = result.stdout.strip().split('\n')
        assert 15 <= len(lines) <= 35, f"Help output has {len(lines)} lines, expected 15-35"
        
        # Verify sections are present and in order
        output = result.stdout.upper()  # Convert to upper for case-insensitive search
        usage_pos = output.find("USAGE:")
        commands_pos = output.find("COMMANDS:")
        options_pos = output.find("OPTIONS:")
        getting_started_pos = output.find("GETTING STARTED:")
        
        # Core sections should exist
        assert usage_pos != -1, "USAGE section not found"
        assert commands_pos != -1, "COMMANDS section not found"
        assert options_pos != -1, "OPTIONS section not found"
        assert getting_started_pos != -1, "GETTING STARTED section not found"
        
        # Sections should appear in logical order
        assert usage_pos < commands_pos < options_pos < getting_started_pos

    def test_version_flag_shows_version(self, kuzu_migrate_path):
        """Test that --version flag shows version information."""
        # Execute
        result = self.run_command([kuzu_migrate_path, "--version"])
        
        # Verify successful exit
        assert result.returncode == 0
        
        # Verify version format
        assert "kuzu-migrate v" in result.stdout
        assert result.stdout.strip().startswith("kuzu-migrate v")

    def test_unknown_command_shows_error_with_help_hint(self, kuzu_migrate_path):
        """Test that unknown command shows error with help hint."""
        # Execute with unknown command
        result = self.run_command([kuzu_migrate_path, "unknown-command"])
        
        # Verify exit code is non-zero (error)
        assert result.returncode != 0
        
        # Verify error message
        assert "ERROR" in result.stderr
        assert "Unknown command: unknown-command" in result.stderr
        
        # Verify help hint
        assert "see --help" in result.stderr

    def test_command_descriptions_are_verb_based(self, kuzu_migrate_path):
        """Test that command descriptions use verb-based phrasing."""
        # Execute
        result = self.run_command([kuzu_migrate_path, "--help"])
        
        # Expected verb patterns for each command
        expected_verbs = {
            "init": ["Create", "Initialize"],
            "apply": ["Execute", "Apply", "Run"],
            "status": ["Check", "Show", "Display"],
            "snapshot": ["Export", "Create", "Save"],
            "rollback": ["Restore", "Rollback", "Revert"]
        }
        
        for cmd, verbs in expected_verbs.items():
            # Find the line with this command
            cmd_line = None
            for line in result.stdout.split('\n'):
                if line.strip().startswith(cmd):
                    cmd_line = line
                    break
            
            assert cmd_line is not None, f"Command '{cmd}' not found in help output"
            
            # Check that at least one expected verb appears
            assert any(verb in cmd_line for verb in verbs), f"No expected verb found for {cmd}: {cmd_line}"

    def test_no_args_shows_concise_usage(self, kuzu_migrate_path):
        """Test that no-args usage is concise and helpful."""
        # Execute
        result = self.run_command([kuzu_migrate_path])
        
        # Verify the output is reasonably sized (not too verbose)
        lines = result.stderr.strip().split('\n')
        assert 15 <= len(lines) <= 35, f"No-args usage has {len(lines)} lines, expected 15-35"
        
        # Verify commands with brief descriptions
        commands = {
            "init": ["Create", "structure"],
            "apply": ["Execute", "pending", "migrations"],
            "status": ["Check", "which", "migrations"],
            "snapshot": ["Export", "database", "backup"],
            "rollback": ["Restore", "snapshot"]
        }
        
        stderr_text = result.stderr
        for cmd, keywords in commands.items():
            assert cmd in stderr_text
            # At least one keyword should appear in the description
            assert any(kw in stderr_text for kw in keywords), f"No descriptive keywords found for {cmd}"
        
        # Verify helpful examples are shown
        assert "kuzu-migrate init" in stderr_text
        assert "kuzu-migrate apply" in stderr_text
        assert "kuzu-migrate status" in stderr_text