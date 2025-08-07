"""汎用的なCLIパラメータ解析ユーティリティ"""

from typing import List, Dict, Any


def parse_parameters(param_strings: List[str]) -> Dict[str, Any]:
    """コマンドライン引数からパラメータを解析
    
    Args:
        param_strings: ['--key=value', 'key2=value2'] 形式の文字列リスト
        
    Returns:
        解析されたパラメータの辞書
        
    Examples:
        >>> parse_parameters(['--id=123', 'name=test', '--active=true'])
        {'id': 123, 'name': 'test', 'active': True}
    """
    params = {}
    
    for param in param_strings:
        if '=' not in param:
            continue
        
        key, value = param.split('=', 1)
        key = key.strip('-')
        
        # 型推定
        if value.lower() in ('true', 'false'):
            params[key] = value.lower() == 'true'
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