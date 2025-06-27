"""
LLM専用エントリーポイント - これ以外使わないでください

使い方:
    echo '{"type": "cypher", "query": "..."}' | LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ python run.py
"""
import sys
import json
import os

# エラーメッセージ
USAGE_ERROR = {
    "status": "error", 
    "score": -1.0,
    "message": "環境変数LD_LIBRARY_PATHが設定されていません",
    "suggestion": "LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ python run.py"
}

# 環境変数チェック
if 'LD_LIBRARY_PATH' not in os.environ:
    print(json.dumps(USAGE_ERROR, ensure_ascii=False))
    sys.exit(1)

# Pythonパスを設定
sys.path.insert(0, '/home/nixos/bin/src')

# mainモジュールを実行
try:
    from requirement.graph.main import main
    main()
except Exception as e:
    error_response = {
        "status": "error",
        "score": -0.5,
        "message": str(e),
        "suggestion": "エラーが発生しました。環境を確認してください"
    }
    print(json.dumps(error_response, ensure_ascii=False))