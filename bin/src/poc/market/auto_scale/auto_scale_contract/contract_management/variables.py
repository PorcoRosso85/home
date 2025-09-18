"""Contract Management Environment Variables and Configuration

This module manages all environment variables and configuration settings
for the contract management system, following the module design conventions.
"""

import os
from pathlib import Path
from typing import TypedDict, Optional


class ContractManagementConfig(TypedDict):
    """Type definition for contract management configuration"""
    # Database configuration
    db_path: str
    db_type: str  # 'memory', 'sqlite', 'kuzu', 'filesystem'
    
    # Query paths
    query_path: Path
    schema_path: Path
    
    # Storage paths
    storage_path: Path
    log_path: Path
    
    # Service configuration
    smtp_host: Optional[str]
    smtp_port: Optional[int]
    smtp_username: Optional[str]
    smtp_password: Optional[str]
    
    # Feature flags
    enable_audit_logging: bool
    enable_email_notifications: bool
    enable_document_generation: bool


def get_config() -> ContractManagementConfig:
    """Get contract management configuration from environment variables
    
    This function reads environment variables and returns a typed configuration.
    Required variables must be set or an error will be raised.
    
    Returns:
        ContractManagementConfig: The configuration dictionary
        
    Raises:
        ValueError: If required environment variables are not set
    """
    # Get base paths
    base_path = Path(__file__).parent
    
    # Database configuration
    db_type = os.environ.get('CONTRACT_DB_TYPE', 'memory')
    if db_type not in ['memory', 'sqlite', 'kuzu', 'filesystem']:
        raise ValueError(f"Invalid CONTRACT_DB_TYPE: {db_type}")
    
    db_path = os.environ.get('CONTRACT_DB_PATH', ':memory:')
    if db_type != 'memory' and not db_path:
        raise ValueError("CONTRACT_DB_PATH is required for non-memory databases")
    
    # Query and schema paths
    query_path = Path(os.environ.get(
        'CONTRACT_QUERY_PATH',
        str(base_path / 'infrastructure' / 'cypher' / 'queries')
    ))
    
    schema_path = Path(os.environ.get(
        'CONTRACT_SCHEMA_PATH',
        str(base_path / 'infrastructure' / 'cypher' / 'schema')
    ))
    
    # Storage paths
    storage_path = Path(os.environ.get(
        'CONTRACT_STORAGE_PATH',
        str(base_path / 'storage')
    ))
    
    log_path = Path(os.environ.get(
        'CONTRACT_LOG_PATH',
        str(base_path / 'logs')
    ))
    
    # Email configuration (optional)
    smtp_host = os.environ.get('CONTRACT_SMTP_HOST')
    smtp_port = int(os.environ.get('CONTRACT_SMTP_PORT', '587')) if smtp_host else None
    smtp_username = os.environ.get('CONTRACT_SMTP_USERNAME')
    smtp_password = os.environ.get('CONTRACT_SMTP_PASSWORD')
    
    # Feature flags
    enable_audit_logging = os.environ.get('CONTRACT_ENABLE_AUDIT_LOGGING', 'true').lower() == 'true'
    enable_email_notifications = os.environ.get('CONTRACT_ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    enable_document_generation = os.environ.get('CONTRACT_ENABLE_DOCUMENT_GENERATION', 'true').lower() == 'true'
    
    return ContractManagementConfig(
        db_path=db_path,
        db_type=db_type,
        query_path=query_path,
        schema_path=schema_path,
        storage_path=storage_path,
        log_path=log_path,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        enable_audit_logging=enable_audit_logging,
        enable_email_notifications=enable_email_notifications,
        enable_document_generation=enable_document_generation,
    )


def get_repository_config() -> dict:
    """Get repository-specific configuration
    
    Returns:
        dict: Configuration for repository initialization
    """
    config = get_config()
    
    return {
        'db_path': config['db_path'],
        'db_type': config['db_type'],
        'query_path': config['query_path'],
        'schema_path': config['schema_path'],
        'storage_path': config['storage_path'],
    }


def get_service_config() -> dict:
    """Get service-specific configuration
    
    Returns:
        dict: Configuration for external services
    """
    config = get_config()
    
    return {
        'smtp': {
            'host': config['smtp_host'],
            'port': config['smtp_port'],
            'username': config['smtp_username'],
            'password': config['smtp_password'],
        },
        'features': {
            'audit_logging': config['enable_audit_logging'],
            'email_notifications': config['enable_email_notifications'],
            'document_generation': config['enable_document_generation'],
        },
        'paths': {
            'log_path': config['log_path'],
        }
    }


# Export configuration functions
__all__ = [
    'ContractManagementConfig',
    'get_config',
    'get_repository_config',
    'get_service_config',
]