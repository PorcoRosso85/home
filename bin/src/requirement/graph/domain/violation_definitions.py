"""
違反定義（ドメイン層）
スコアとメッセージの定義
"""

# 違反タイプごとの定義
VIOLATION_DEFINITIONS = {
    "graph_depth_exceeded": {
        "score": -100,
        "message": "グラフ深さ制限超過: 許可された深さを超える依存関係が検出されました"
    },
    "self_reference": {
        "score": -100,
        "message": "自己参照: ノードが自分自身に依存しています"
    },
    "circular_reference": {
        "score": -100,
        "message": "循環参照: 依存関係に循環が検出されました"
    },
    "invalid_dependency": {
        "score": -50,
        "message": "無効な依存関係: 許可されていない依存関係が検出されました"
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