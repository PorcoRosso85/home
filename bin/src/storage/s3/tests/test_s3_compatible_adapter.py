"""Tests for S3-compatible storage adapter."""

import pytest
from unittest.mock import Mock, patch
from s3_client.s3_compatible_adapter import S3CompatibleAdapter, detect_provider


class TestS3CompatibleAdapter:
    """Test the S3-compatible storage adapter."""
    
    def test_detect_provider_aws(self):
        """Test AWS S3 provider detection."""
        assert detect_provider(None) == "AWS S3"
        assert detect_provider("") == "AWS S3"
    
    def test_detect_provider_minio(self):
        """Test MinIO provider detection."""
        assert detect_provider("http://localhost:9000") == "MinIO"
        assert detect_provider("https://minio.example.com") == "MinIO"
    
    def test_detect_provider_r2(self):
        """Test Cloudflare R2 provider detection."""
        assert detect_provider("https://account.r2.cloudflarestorage.com") == "Cloudflare R2"
    
    def test_detect_provider_backblaze(self):
        """Test Backblaze B2 provider detection."""
        assert detect_provider("https://s3.us-west-002.backblazeb2.com") == "Backblaze B2"
    
    def test_s3_adapter_implements_interface(self):
        """Test that S3CompatibleAdapter implements StorageAdapter."""
        from s3_client import StorageAdapter
        
        # Mock boto3 client
        mock_client = Mock()
        adapter = S3CompatibleAdapter(mock_client, "test-bucket")
        
        # Verify it implements the protocol
        assert isinstance(adapter, StorageAdapter)
    
    @patch('boto3.client')
    def test_s3_adapter_put_object(self, mock_boto_client):
        """Test putting an object via S3 adapter."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        adapter = S3CompatibleAdapter(mock_s3, "test-bucket")
        adapter.put_object("test.txt", b"data", {"type": "text"})
        
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test.txt",
            Body=b"data",
            Metadata={"type": "text"}
        )
    
    def test_s3_adapter_get_provider_name(self):
        """Test provider name detection."""
        mock_client = Mock()
        
        # Test with different endpoints
        adapter = S3CompatibleAdapter(mock_client, "bucket", endpoint_url="http://localhost:9000")
        assert adapter.get_provider_name() == "MinIO"
        
        adapter = S3CompatibleAdapter(mock_client, "bucket", endpoint_url=None)
        assert adapter.get_provider_name() == "AWS S3"