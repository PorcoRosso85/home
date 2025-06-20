# ログレベル定数定義（言語非依存）
# CONVENTION.yaml準拠：定数はUPPER_SNAKE_CASE

LOG_LEVELS = {
    'TRACE': 0,  # 最も詳細なデバッグ情報
    'DEBUG': 1,  # デバッグ情報
    'INFO': 2,   # 一般的な情報
    'WARN': 3,   # 警告
    'ERROR': 4,  # エラー
    'FATAL': 5,  # 致命的エラー
    'OFF': 99    # ログ出力無効
}

# 逆引き用辞書（数値からレベル名を取得）
LEVEL_NAMES = {v: k for k, v in LOG_LEVELS.items()}

def get_level_value(level_name):
    """レベル名から数値を取得（大文字小文字を許容）"""
    return LOG_LEVELS.get(level_name.upper(), LOG_LEVELS['INFO'])

def get_level_name(level_value):
    """数値からレベル名を取得"""
    return LEVEL_NAMES.get(level_value, 'UNKNOWN')