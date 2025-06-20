# 高度な設定パーサー（階層、除外構文、パターンマッチ）
# CONVENTION.yaml準拠：関数ベース実装

from .levels import get_level_value
from .config import parse_log_config

def parse_advanced_config(config_string=None):
    """高度なLOG_CONFIG環境変数をパース
    
    追加機能:
    - 階層的設定: "app.service:TRACE,app:DEBUG"
    - 部分一致: "app*:DEBUG" 
    - 複合ルール: "*:WARN,domain:INFO,-infrastructure"
    
    Args:
        config_string: 設定文字列（省略時は環境変数から取得）
    
    Returns:
        dict: パース結果 {
            'exact_rules': 完全一致ルール,
            'pattern_rules': パターンルール,
            'hierarchy_rules': 階層ルール,
            'excludes': 除外集合,
            'exclude_patterns': 除外パターン
        }
    """
    # 基本パーサーで初期処理
    basic_rules, basic_excludes = parse_log_config(config_string)
    
    exact_rules = {}
    pattern_rules = []
    hierarchy_rules = {}
    excludes = set()
    exclude_patterns = []
    
    # ルールを分類
    for module, level_value in basic_rules.items():
        if '*' in module and module != '*':
            # パターンルール（app* など）
            pattern = module.replace('*', '')
            pattern_rules.append((pattern, level_value))
        elif '.' in module:
            # 階層ルール（app.service など）
            hierarchy_rules[module] = level_value
            exact_rules[module] = level_value
        else:
            # 完全一致ルール
            exact_rules[module] = level_value
    
    # 除外ルールも分類
    for exclude in basic_excludes:
        if '*' in exclude:
            pattern = exclude.replace('*', '')
            exclude_patterns.append(pattern)
        else:
            excludes.add(exclude)
    
    return {
        'exact_rules': exact_rules,
        'pattern_rules': sorted(pattern_rules, key=lambda x: -len(x[0])),  # 長い順
        'hierarchy_rules': hierarchy_rules,
        'excludes': excludes,
        'exclude_patterns': exclude_patterns
    }

def should_log_advanced(module, level, parsed_config):
    """高度な判定ロジック
    
    Args:
        module: モジュール名
        level: ログレベル名
        parsed_config: parse_advanced_configの結果
    
    Returns:
        bool: ログ出力すべきならTrue
    """
    level_value = get_level_value(level)
    
    # 除外チェック（最優先）
    if module in parsed_config['excludes']:
        return False
    
    # 除外パターンチェック
    for pattern in parsed_config['exclude_patterns']:
        if module.startswith(pattern):
            return False
    
    # 完全一致チェック
    if module in parsed_config['exact_rules']:
        return level_value >= parsed_config['exact_rules'][module]
    
    # 階層チェック（app.service.user → app.service → app）
    if '.' in module:
        parts = module.split('.')
        for i in range(len(parts), 0, -1):
            parent = '.'.join(parts[:i])
            if parent in parsed_config['hierarchy_rules']:
                return level_value >= parsed_config['hierarchy_rules'][parent]
    
    # パターンマッチチェック
    for pattern, pattern_level in parsed_config['pattern_rules']:
        if module.startswith(pattern):
            return level_value >= pattern_level
    
    # ワイルドカードチェック
    if '*' in parsed_config['exact_rules']:
        return level_value >= parsed_config['exact_rules']['*']
    
    # ルールがない場合は出力しない
    return False

def validate_config(config_string):
    """設定文字列の妥当性をチェック
    
    Args:
        config_string: 検証する設定文字列
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    if not config_string:
        return True, []
    
    for rule in config_string.split(','):
        rule = rule.strip()
        if not rule:
            continue
        
        # 除外ルール
        if rule.startswith('-'):
            if len(rule) == 1:
                errors.append(f"除外ルールが空です: '{rule}'")
            continue
        
        # module:level 形式チェック
        if ':' in rule:
            parts = rule.split(':', 1)
            module, level = parts[0], parts[1].upper()
            
            if not module:
                errors.append(f"モジュール名が空です: '{rule}'")
            
            if level not in ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL', 'OFF']:
                errors.append(f"不正なログレベル: '{level}' in '{rule}'")
    
    return len(errors) == 0, errors