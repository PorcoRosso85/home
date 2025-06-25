"""RGL実行用スクリプト - uvで直接実行可能"""

import sys
import os

# uvを使わずに直接実行された場合の案内
if not os.environ.get('VIRTUAL_ENV') and not os.environ.get('UV_PROJECT_ROOT'):
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("RGL - 開発決定事項管理ツール")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("実行方法: uv run python run.py [コマンド]")
    print()
    print("例:")
    print("  uv run python run.py --help     # ヘルプ表示")
    print("  uv run python run.py list       # 決定事項一覧")
    print("  uv run python run.py add \"...\"  # 新規追加")
    print()
    print("初回実行時は自動的に環境構築されます。")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    sys.exit(0)

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CLIをインポートして実行
from poc.requirement_graph_logic.decision_cli import main

if __name__ == "__main__":
    main()