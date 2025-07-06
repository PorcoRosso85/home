"""
違反定義（ドメイン層）
スコアとメッセージの定義
"""

# 違反タイプごとの定義
VIOLATION_DEFINITIONS = {
    "hierarchy_violation": {
        "score": -100,
        "message": "階層違反: 下位階層が上位階層に依存しています"
    },
    "self_reference": {
        "score": -100,
        "message": "自己参照: ノードが自分自身に依存しています"
    },
    "circular_reference": {
        "score": -100,
        "message": "循環参照: 依存関係に循環が検出されました"
    },
    "title_level_mismatch": {
        "score": -30,
        "message": "タイトル不整合: タイトルと階層レベルが一致しません"
    },
    "constraint_violations": {
        "score_per_violation": -20,
        "message": "制約違反が検出されました"
    },
    "no_violation": {
        "score": 0,
        "message": "問題ありません"
    }
}