# 基本環境変数パーサー
# CONVENTION.yaml準拠：デフォルト設定禁止、関数ベース実装

import os
from .levels import get_level_value

def parse_log_config(config_string=None):
    """基本的なLOG_CONFIG環境変数をパース
    
    構文: "module:level,module:level,..."
    例: "*:INFO,domain:DEBUG,application:TRACE"
    
    Args:
        config_string: 設定文字列（省略時は環境変数から取得）
    
    Returns:
        tuple: (rules辞書, excludes集合)
    """
    if config_string is None:
        config_string = os.getenv('LOG_CONFIG')
        if not config_string:
            # CONVENTION.yaml: デフォルト設定禁止
            return {}, set()
    
    rules = {}
    excludes = set()
    
    # カンマで分割して各ルールを処理
    for rule in config_string.split(','):
        rule = rule.strip()
        if not rule:
            continue
        
        # 除外ルール（-prefix）
        if rule.startswith('-'):
            excludes.add(rule[1:])
            continue
        
        # module:level 形式
        parts = rule.split(':', 1)
        module = parts[0]
        level = parts[1].upper() if len(parts) > 1 else 'INFO'
        
        # レベル値を取得（不正な値はINFOになる）
        level_value = get_level_value(level)
        rules[module] = level_value
    
    return rules, excludes

def should_log(module, level, rules, excludes):
    """指定されたモジュールとレベルでログ出力すべきか判定
    
    Args:
        module: モジュール名
        level: ログレベル名（文字列）
        rules: ルール辞書（module -> level_value）
        excludes: 除外モジュール集合
    
    Returns:
        bool: ログ出力すべきならTrue
    """
    # 除外チェック
    if module in excludes:
        return False
    
    level_value = get_level_value(level)
    
    # 完全一致チェック
    if module in rules:
        return level_value >= rules[module]
    
    # ワイルドカードチェック
    if '*' in rules:
        return level_value >= rules['*']
    
    # ルールがない場合は出力しない（デフォルト設定禁止）
    return False

def get_config_info():
    """現在の設定情報を取得（デバッグ用）
    
    Returns:
        dict: 設定情報
    """
    config_string = os.getenv('LOG_CONFIG', '')
    rules, excludes = parse_log_config(config_string)
    
    return {
        'raw_config': config_string,
        'rules': {k: get_level_value(v) if isinstance(v, str) else v for k, v in rules.items()},
        'excludes': list(excludes),
        'is_configured': bool(config_string)
    }