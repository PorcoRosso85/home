#!/usr/bin/env python3
"""
Vessel with structured logging - 規約準拠版
"""
import sys
from vessel_log import VesselLogger

# ロガーの初期化
logger = VesselLogger(vessel_type="vessel")

def main():
    # 標準入力からスクリプトを読み込む
    logger.debug("Reading script from stdin")
    script = sys.stdin.read()
    logger.debug(f"Script length: {len(script)} chars")
    
    # 実行環境を準備
    context = {
        '__name__': '__main__',
        'vessel': True,
        # print関数をラップして構造化ログ対応
        'print': logger.output
    }
    
    # スクリプトを実行
    try:
        logger.debug("Executing script")
        exec(script, context)
        logger.debug("Script execution completed")
    except Exception as e:
        logger.error("Script execution failed", error=e)
        sys.exit(1)

if __name__ == "__main__":
    main()