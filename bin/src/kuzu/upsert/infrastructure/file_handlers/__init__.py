"""
ファイルハンドラーパッケージ

各種ファイル形式に対応した読み込み処理を提供します。
各ファイル形式ごとのハンドラーと、それらを統合するファクトリーで構成されています。
"""

from upsert.infrastructure.file_handlers.factory import create_file_handler, get_supported_extensions
from upsert.infrastructure.file_handlers.base import FileHandler, FileLoadResult
