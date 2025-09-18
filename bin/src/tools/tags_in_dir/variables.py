"""Environment variables and configuration."""

import os
from typing import TypedDict, Optional


class Config(TypedDict):
    """Application configuration."""
    ctags_path: str
    default_db_path: str
    default_extensions: list[str]
    max_file_size: int
    export_chunk_size: int


def get_config() -> Config:
    """
    Get application configuration from environment variables.
    
    Returns:
        Configuration dictionary
    """
    return Config(
        ctags_path=os.environ.get('TAGS_IN_DIR_CTAGS_PATH', 'ctags'),
        default_db_path=os.environ.get('TAGS_IN_DIR_DB_PATH', ':memory:'),
        default_extensions=os.environ.get(
            'TAGS_IN_DIR_EXTENSIONS',
            '.py,.js,.ts,.java,.c,.cpp,.go,.rs'
        ).split(','),
        max_file_size=int(os.environ.get('TAGS_IN_DIR_MAX_FILE_SIZE', '10485760')),  # 10MB
        export_chunk_size=int(os.environ.get('TAGS_IN_DIR_EXPORT_CHUNK_SIZE', '1000'))
    )