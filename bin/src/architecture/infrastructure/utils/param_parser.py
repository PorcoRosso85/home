
'汎用的なCLIパラメータ解析ユーティリティ'
from typing import List, Dict, Any
import logging
logger = logging.getLogger(__name__)

def parse_parameters(param_strings: List[str]) -> Dict[(str, Any)]:
    "コマンドライン引数からパラメータを解析\n    \n    Args:\n        param_strings: ['--key=value', 'key2=value2'] 形式の文字列リスト\n        \n    Returns:\n        解析されたパラメータの辞書\n        \n    Examples:\n        >>> parse_parameters(['--id=123', 'name=test', '--active=true'])\n        {'id': 123, 'name': 'test', 'active': True}\n    "
    params = {}
    for param in param_strings:
        if ('=' not in param):
            continue
        (key, value) = param.split('=', 1)
        key = key.strip('-')
        if (value.lower() in ('true', 'false')):
            params[key] = (value.lower() == 'true')
        elif value.isdigit():
            params[key] = int(value)
        elif value.replace('.', '').replace('-', '').isdigit():
            try:
                params[key] = float(value)
            except ValueError:
                params[key] = value
        else:
            params[key] = value
    return params
