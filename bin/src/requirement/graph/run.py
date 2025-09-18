"""
Cypherクエリエントリーポイント

使い方:
    echo '{"type": "cypher", "query": "..."}' | python run.py
    echo '{"type": "schema", "action": "apply"}' | python run.py
"""
import sys
import json

# Pythonパスを親ディレクトリに設定（相対インポート解決のため）
sys.path.insert(0, '/home/nixos/bin/src')

# loggerインポート
from requirement.graph.infrastructure.logger import info, error

try:
    # メインモジュールを実行
    from requirement.graph.main import main
    info("rgl.run", "Starting requirement graph runner")
    main()
except EnvironmentError as e:
    # 環境変数エラーを適切にフォーマット
    error("rgl.run", str(e), 
          suggestion="必要な環境変数を設定してください")
    sys.exit(1)
except Exception as e:
    # その他のエラー
    error("rgl.run", str(e),
          suggestion="エラーが発生しました。環境を確認してください")
    sys.exit(1)
