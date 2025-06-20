# 設定パーサー（ファイル名と同じ関数名）
# CONVENTION.yaml準拠：モジュール名=ファイル名=関数名

from .parser import parse_advanced_config as _parse_advanced

def parse(config_string):
    """設定文字列をパース
    
    使用例:
        # 基本的な使用
        result = parse("*:INFO")
        # => {'exact_rules': {'*': 2}, 'excludes': set(), ...}
        
        # 複数モジュール指定
        result = parse("app:DEBUG,domain:TRACE")
        # => {'exact_rules': {'app': 1, 'domain': 0}, ...}
        
        # 除外と階層指定
        result = parse("*:WARN,-infrastructure,app.service:TRACE")
        # => {'exact_rules': {'*': 3, 'app.service': 0}, 'excludes': {'infrastructure'}, ...}
    
    引数:
        config_string: "module:level,..." 形式の文字列、またはNone（環境変数から取得）
    
    戻り値:
        パース結果の辞書 {
            'exact_rules': 完全一致ルール,
            'pattern_rules': パターンルール,
            'hierarchy_rules': 階層ルール,
            'excludes': 除外集合,
            'exclude_patterns': 除外パターン
        }
    """
    return _parse_advanced(config_string)