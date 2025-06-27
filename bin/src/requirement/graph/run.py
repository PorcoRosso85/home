"""
LLM専用エントリーポイント - これ以外使わないでください

使い方:
    echo '{"type": "cypher", "query": "..."}' | LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ RGL_DB_PATH=./rgl_db python run.py
"""
import sys
import os
import json

# Pythonパスを親ディレクトリに設定（相対インポート解決のため）
sys.path.insert(0, '/home/nixos/bin/src')

try:
    # メインモジュールを実行
    from requirement.graph.main import main
    main()
except EnvironmentError as e:
    # 環境変数エラーを適切にフォーマット
    error_response = {
        "status": "error",
        "score": -1.0,
        "message": str(e),
        "suggestion": "必要な環境変数を設定してください"
    }
    print(json.dumps(error_response, ensure_ascii=False))
    sys.exit(1)
except Exception as e:
    # その他のエラー
    error_response = {
        "status": "error",
        "score": -0.5,
        "message": str(e),
        "suggestion": "エラーが発生しました。環境を確認してください"
    }
    print(json.dumps(error_response, ensure_ascii=False))
    sys.exit(1)