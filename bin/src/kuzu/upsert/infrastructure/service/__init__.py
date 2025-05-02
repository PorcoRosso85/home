"""
ファイル読み込みサービスパッケージ

各種ファイル形式に対応した読み込みサービスを提供します。
CONVENTION.yamlの規約に準拠し、関数型プログラミングアプローチで実装されています。
"""

# サービスをインポートして公開
from upsert.infrastructure.service import yaml_service
from upsert.infrastructure.service import json_service
from upsert.infrastructure.service import json5_service
from upsert.infrastructure.service import jsonl_service
from upsert.infrastructure.service import csv_service
from upsert.infrastructure.service.file_loader import (
    load_file, 
    get_supported_extensions, 
    get_flat_supported_extensions,
    get_loader_function_for_extension,
    get_service_name_for_extension,
    check_extension_support
)

