"""
違反コード定義（ドメイン層）
整数ベースの違反コード体系
"""


class ViolationCode:
    """違反コード定数"""
    # 構造違反 (1xxx)
    GRAPH_DEPTH_EXCEEDED = 1001
    SELF_REFERENCE = 1002
    CIRCULAR_REFERENCE = 1003
    INVALID_DEPENDENCY = 1004
    
    # 整合性違反 (2xxx)
    MISSING_DEPENDENCY = 2001
    
    # 規約違反 (3xxx)
    NAMING_CONVENTION = 3001
    
    # 正常 (9xxx)
    NO_VIOLATION = 9000


# 違反コードと基本スコアのマッピング
_VIOLATION_SCORES = {
    1001: -100,  # グラフ深さ制限超過
    1002: -100,  # 自己参照
    1003: -100,  # 循環参照
    1004: -50,   # 無効な依存関係
    2001: -40,   # 依存関係不足
    3001: -10,   # 命名規約違反
    9000: 0      # 違反なし
}


def get_base_score(violation_code: int) -> int:
    """
    違反コードから基本スコアを取得
    
    Args:
        violation_code: 4桁の違反コード
        
    Returns:
        基本スコア（負の整数）
    """
    return _VIOLATION_SCORES.get(violation_code, 0)


def get_violation_level(violation_code: int) -> int:
    """
    違反レベルを取得（1-5の整数）
    
    Args:
        violation_code: 4桁の違反コード
        
    Returns:
        違反レベル（1=正常、5=重大違反）
    """
    if violation_code >= 9000:
        return 1  # 正常
    elif violation_code >= 3000:
        return 2  # 軽微
    elif violation_code >= 2000:
        return 3  # 中程度
    elif violation_code >= 1000:
        return 5  # 重大
    else:
        return 1  # デフォルト