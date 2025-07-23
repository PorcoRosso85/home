#!/usr/bin/env python3
"""
インフラストラクチャ層

KuzuDBとの接続、VECTOR拡張、埋め込み生成など外部システムとの統合を提供
"""

# Database operations
from .db import (
    DatabaseConfig,
    create_kuzu_database,
    create_kuzu_connection,
    close_connection,
    count_documents,
    IN_MEMORY_DB_PATH,
    EMBEDDING_DIMENSION
)

# Vector operations
from .vector import (
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    VECTOR_EXTENSION_NAME,
    DOCUMENT_TABLE_NAME,
    DOCUMENT_EMBEDDING_INDEX_NAME
)

# Embedding operations
from .embedding import (
    create_embedding_service,
    create_standalone_embedding_service,
    EmbeddingResult,
    DEFAULT_MODEL_NAME
)

# Configuration management
from .variables import (
    VSSConfig,
    create_config,
    get_default_config,
    merge_config,
    validate_config,
    config_to_dict,
    EnvironmentVariables,
    load_environment_variables,
    get_current_environment
)

__all__ = [
    # Database
    'DatabaseConfig',
    'create_kuzu_database',
    'create_kuzu_connection',
    'close_connection',
    'count_documents',
    'IN_MEMORY_DB_PATH',
    'EMBEDDING_DIMENSION',
    # Vector
    'check_vector_extension',
    'initialize_vector_schema',
    'insert_documents_with_embeddings',
    'search_similar_vectors',
    'VECTOR_EXTENSION_NAME',
    'DOCUMENT_TABLE_NAME',
    'DOCUMENT_EMBEDDING_INDEX_NAME',
    # Embedding
    'create_embedding_service',
    'create_standalone_embedding_service',
    'EmbeddingResult',
    'DEFAULT_MODEL_NAME',
    # Configuration
    'VSSConfig',
    'create_config',
    'get_default_config',
    'merge_config',
    'validate_config',
    'config_to_dict',
    'EnvironmentVariables',
    'load_environment_variables',
    'get_current_environment'
]