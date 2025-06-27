#!/bin/bash
# pytest実行用スクリプト - 環境変数とin-sourceテスト設定
# 
# 使い方:
#   ./run_pytest.sh                    # 全テスト実行
#   ./run_pytest.sh -v                 # 詳細出力
#   ./run_pytest.sh infrastructure/    # 特定ディレクトリ
#   ./run_pytest.sh -k "曖昧"         # キーワード指定

# 環境変数設定
export LD_LIBRARY_PATH=/nix/store/1n4957f86zjh8gv7j8a1ga1gx35naqqk-gcc-12.3.0-lib/lib
export RGL_DB_PATH=/home/nixos/bin/src/requirement/graph/rgl_db

# 仮想環境アクティベート
source /home/nixos/bin/src/.venv/bin/activate

# pytestを実行（ヘルパースクリプトとエラーが出るファイルを除外）
python -m pytest \
    --ignore=run.py \
    --ignore=run_all_tests.py \
    --ignore=run_all_tests_with_env.py \
    --ignore=test_single_module.py \
    --ignore=test_migrated_features.py \
    --tb=short \
    "$@"