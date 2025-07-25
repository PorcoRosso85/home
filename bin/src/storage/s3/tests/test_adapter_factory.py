"""Tests for storage adapter factory."""

import pytest
import os
from unittest.mock import patch, Mock
from s3_client.adapter_factory import create_storage_adapter


class TestAdapterFactory:
    """Test the storage adapter factory function."""
    
    def test_create_in_memory_adapter_by_default(self):
        """Test that in-memory adapter is created when no S3 config."""
        with patch.dict(os.environ, {}, clear=True):
            adapter = create_storage_adapter()
            assert adapter.get_provider_name() == "in-memory"
    
    def test_create_s3_adapter_with_aws_credentials(self):
        """Test S3 adapter creation with AWS credentials."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret',
            'S3_BUCKET': 'test-bucket'
        }):
            with patch('boto3.client') as mock_boto:
                mock_client = Mock()
                mock_boto.return_value = mock_client
                
                adapter = create_storage_adapter()
                assert adapter.get_provider_name() == "AWS S3"
                mock_boto.assert_called_once()
    
    def test_create_minio_adapter(self):
        """Test MinIO adapter creation."""
        with patch.dict(os.environ, {
            'S3_ENDPOINT': 'http://localhost:9000',
            'AWS_ACCESS_KEY_ID': 'minioadmin',
            'AWS_SECRET_ACCESS_KEY': 'minioadmin',
            'S3_BUCKET': 'test-bucket'
        }):
            with patch('boto3.client') as mock_boto:
                mock_client = Mock()
                mock_boto.return_value = mock_client
                
                adapter = create_storage_adapter()
                assert adapter.get_provider_name() == "MinIO"
    
    def test_create_r2_adapter(self):
        """Test Cloudflare R2 adapter creation."""
        with patch.dict(os.environ, {
            'S3_ENDPOINT': 'https://account.r2.cloudflarestorage.com',
            'AWS_ACCESS_KEY_ID': 'r2-key',
            'AWS_SECRET_ACCESS_KEY': 'r2-secret',
            'S3_BUCKET': 'test-bucket'
        }):
            with patch('boto3.client') as mock_boto:
                mock_client = Mock()
                mock_boto.return_value = mock_client
                
                adapter = create_storage_adapter()
                assert adapter.get_provider_name() == "Cloudflare R2"
    
    def test_create_adapter_with_explicit_type(self):
        """Test creating adapter with explicit type parameter."""
        # Force in-memory even with S3 credentials
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'S3_BUCKET': 'test-bucket'
        }):
            adapter = create_storage_adapter(adapter_type="in-memory")
            assert adapter.get_provider_name() == "in-memory"
    
    def test_missing_bucket_raises_error(self):
        """Test that missing bucket config raises error for S3."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret'
        }, clear=True):
            with pytest.raises(ValueError, match="S3_BUCKET"):
                create_storage_adapter()