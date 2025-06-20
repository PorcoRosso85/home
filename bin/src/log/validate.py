# 設定検証（ファイル名と同じ関数名）
# CONVENTION.yaml準拠：モジュール名=ファイル名=関数名

from .parser import validate_config as _validate_config

def validate(config_string):
    """ログ設定文字列の妥当性を検証
    
    使用例:
        # 正しい設定
        is_valid, errors = validate("*:INFO,domain:DEBUG")
        # => (True, [])
        
        # 不正なレベル名
        is_valid, errors = validate("app:INVALID")
        # => (False, ["不正なログレベル: 'INVALID' in 'app:INVALID'"])
        
        # 空のモジュール名
        is_valid, errors = validate(":INFO")
        # => (False, ["モジュール名が空です: ':INFO'"])
    
    引数:
        config_string: 検証する設定文字列
    
    戻り値:
        タプル (is_valid: bool, error_messages: list)
    """
    return _validate_config(config_string)