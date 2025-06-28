"""
CLIエントリーポイント
パッケージとして実行することで相対インポートを維持
"""
import sys
import os
import runpy

# requirement/graphディレクトリの親を追加
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def main():
    """エントリーポイント - requirement.graph.mainとして実行"""
    # モジュールとして実行（相対インポートが機能する）
    runpy.run_module('requirement.graph.main', run_name='__main__')


def schema_main():
    """スキーマ適用エントリーポイント"""
    runpy.run_module('requirement.graph.infrastructure.apply_ddl_schema', run_name='__main__')


if __name__ == "__main__":
    main()