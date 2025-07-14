#!/usr/bin/env python3
"""Contract testing use cases demonstration.

This test file serves as executable documentation for the contract testing system.
Each test demonstrates a specific use case with ajv-cli.
"""
import pytest
import subprocess
import json
import tempfile
import os
from pathlib import Path


@pytest.fixture
def test_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def log_schema(test_dir):
    """Sample schema for logging contract."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["timestamp", "level", "message"],
        "properties": {
            "timestamp": {"type": "string", "format": "date-time"},
            "level": {"enum": ["DEBUG", "INFO", "WARN", "ERROR"]},
            "message": {"type": "string"},
            "context": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "required": ["id"],
                        "properties": {
                            "id": {"type": "string"},
                            "role": {"enum": ["admin", "user", "guest"]}
                        }
                    }
                }
            }
        }
    }
    
    schema_file = Path(test_dir) / "log.schema.json"
    schema_file.write_text(json.dumps(schema))
    return str(schema_file)


@pytest.fixture
def producer_script(test_dir):
    """Factory for creating producer scripts."""
    def _create_producer(content: str) -> str:
        script_path = Path(test_dir) / "producer.sh"
        script_path.write_text(f"#!/bin/bash\n{content}")
        script_path.chmod(0o755)
        return str(script_path)
    return _create_producer


class TestProducerValidation:
    """Test cases for producer output validation."""
    
    def test_valid_producer_output(self, log_schema, producer_script):
        """Producer generates valid log entry that passes schema validation.
        
        Example:
            A logger tool outputs JSON that conforms to the contract.
        """
        producer = producer_script('''
cat << EOF
{
  "timestamp": "2025-01-14T12:00:00Z",
  "level": "INFO",
  "message": "User logged in",
  "context": {
    "user": {
      "id": "user123",
      "role": "admin"
    }
  }
}
EOF
        ''')
        
        result = subprocess.run(
            ["nix", "run", ".#test-producer", "--", log_schema, producer],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Producer validation failed: {result.stderr}"
        assert "✅ Producer output is valid" in result.stdout
    
    @pytest.mark.parametrize("missing_field,json_output", [
        ("message", '{"timestamp": "2025-01-14T12:00:00Z", "level": "INFO"}'),
        ("level", '{"timestamp": "2025-01-14T12:00:00Z", "message": "test"}'),
        ("timestamp", '{"level": "INFO", "message": "test"}'),
    ])
    def test_missing_required_fields(self, log_schema, producer_script, missing_field, json_output):
        """Producer with missing required field fails validation.
        
        Validates that each required field is enforced by the schema.
        """
        producer = producer_script(f'echo \'{json_output}\'')
        
        result = subprocess.run(
            ["nix", "run", ".#test-producer", "--", log_schema, producer],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "❌ Producer output violates contract" in result.stdout
        # ajv-cli reports which field is missing
        assert missing_field in result.stderr
    
    @pytest.mark.parametrize("level", ["FATAL", "TRACE", "invalid", ""])
    def test_invalid_enum_values(self, log_schema, producer_script, level):
        """Producer with invalid enum value fails validation.
        
        Only DEBUG, INFO, WARN, ERROR are allowed log levels.
        """
        producer = producer_script(f'''
cat << EOF
{{
  "timestamp": "2025-01-14T12:00:00Z",
  "level": "{level}",
  "message": "Test message"
}}
EOF
        ''')
        
        result = subprocess.run(
            ["nix", "run", ".#test-producer", "--", log_schema, producer],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "enum" in result.stderr.lower()


class TestConsumerValidation:
    """Test cases for consumer input validation."""
    
    def test_valid_consumer_input(self, log_schema, test_dir):
        """Consumer input validation ensures only valid data is processed.
        
        This protects consumers from malformed input.
        """
        test_data = {
            "timestamp": "2025-01-14T12:00:00Z",
            "level": "ERROR",
            "message": "Database connection failed"
        }
        
        data_file = Path(test_dir) / "test.json"
        data_file.write_text(json.dumps(test_data))
        
        result = subprocess.run(
            ["nix", "run", ".#test-consumer", "--", log_schema, str(data_file)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "✅ Test data is valid for consumer" in result.stdout


class TestContractIntegration:
    """End-to-end contract testing scenarios."""
    
    def test_producer_consumer_pipeline(self, log_schema, producer_script, test_dir):
        """Full contract test: producer → consumer pipeline.
        
        Verifies the entire data flow works with valid contracts.
        """
        producer = producer_script('''
cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "level": "WARN",
  "message": "High memory usage detected"
}
EOF
        ''')
        
        # Consumer that processes log entries
        consumer_script = Path(test_dir) / "consumer.sh"
        consumer_script.write_text('''#!/bin/bash
input=$(cat)
# Check if it's valid JSON
echo "$input" | jq -e . > /dev/null || exit 1
# Extract and print message
echo "$input" | jq -r '.message'
''')
        consumer_script.chmod(0o755)
        
        result = subprocess.run(
            ["nix", "run", ".#contract-test", "--", 
             log_schema, producer, str(consumer_script)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "✅ Contract test passed!" in result.stdout
    
    def test_nested_object_validation(self, log_schema, producer_script):
        """Complex nested objects are validated correctly.
        
        Tests deep schema validation for context.user.role enum.
        """
        producer = producer_script('''
cat << EOF
{
  "timestamp": "2025-01-14T12:00:00Z",
  "level": "INFO",
  "message": "Permission check",
  "context": {
    "user": {
      "id": "admin001",
      "role": "invalid-role"
    }
  }
}
EOF
        ''')
        
        result = subprocess.run(
            ["nix", "run", ".#test-producer", "--", log_schema, producer],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "enum" in result.stderr.lower()


class TestSchemaEvolution:
    """Demonstrate how contract testing helps with schema evolution."""
    
    def test_backward_compatible_addition(self, test_dir, producer_script):
        """Adding optional fields maintains backward compatibility.
        
        Old producers continue to work with new schemas.
        """
        # V1 schema - basic
        v1_schema = {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        # V2 schema - added optional email
        v2_schema = {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            }
        }
        
        # Save schemas
        v1_file = Path(test_dir) / "v1.schema.json"
        v2_file = Path(test_dir) / "v2.schema.json"
        v1_file.write_text(json.dumps(v1_schema))
        v2_file.write_text(json.dumps(v2_schema))
        
        # Old producer (V1 compatible)
        producer = producer_script('echo \'{"name": "Alice"}\'')
        
        # Should work with both V1 and V2 schemas
        for schema in [v1_file, v2_file]:
            result = subprocess.run(
                ["nix", "run", ".#test-producer", "--", str(schema), producer],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Failed with {schema.name}: {result.stderr}"