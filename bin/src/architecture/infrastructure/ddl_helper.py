
'DDL Helper functions for KuzuDB operations.'
import re
from typing import Any
import logging
logger = logging.getLogger(__name__)

def execute_ddl_file(conn: Any, path: str) -> None:
    'Execute DDL file with multiple statements.\n    \n    Args:\n        conn: KuzuDB connection object\n        path: Path to DDL file\n        \n    Features:\n    - Split statements by semicolon\n    - Remove comments (-- and /* */)\n    - Ignore "already exists" errors\n    '
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = _remove_comments(content)
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
    for statement in statements:
        try:
            conn.execute(statement)
        except Exception as e:
            if ('already exists' not in str(e).lower()):
                raise

def _remove_comments(content: str) -> str:
    'Remove SQL comments from content.\n    \n    Args:\n        content: SQL content with comments\n        \n    Returns:\n        Content with comments removed\n    '
    content = re.sub('--.*?(?=\\n|$)', '', content)
    content = re.sub('/\\*.*?\\*/', '', content, flags=re.DOTALL)
    return content
