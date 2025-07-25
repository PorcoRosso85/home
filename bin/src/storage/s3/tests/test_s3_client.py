"""Basic tests for S3 client module."""

import pytest
from s3_client import S3Client, S3ClientConfig


def test_import_s3_client():
    """Test that S3Client can be imported."""
    assert S3Client is not None
    assert S3ClientConfig is not None


def test_s3_client_config_creation():
    """Test S3ClientConfig creation with defaults."""
    config = S3ClientConfig()
    assert config.region_name == "us-east-1"
    assert config.bucket_name == "default-bucket"
    assert config.endpoint_url is None
    assert config.access_key_id is None
    assert config.secret_access_key is None


def test_s3_client_config_custom():
    """Test S3ClientConfig with custom values."""
    config = S3ClientConfig(
        endpoint_url="http://localhost:9000",
        access_key_id="test-key",
        secret_access_key="test-secret",
        region_name="us-west-2",
        bucket_name="test-bucket"
    )
    assert config.endpoint_url == "http://localhost:9000"
    assert config.access_key_id == "test-key"
    assert config.secret_access_key == "test-secret"
    assert config.region_name == "us-west-2"
    assert config.bucket_name == "test-bucket"


def test_s3_client_protocol():
    """Test that S3Client is a Protocol."""
    # Verify it's a Protocol by checking for required methods
    required_methods = ["put_object", "get_object", "delete_object", "list_objects"]
    for method in required_methods:
        assert hasattr(S3Client, method)