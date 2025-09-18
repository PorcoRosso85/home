#!/usr/bin/env python3
"""
Data-aware Vessel with structured logging - 規約準拠版
"""
import sys
from vessel_log import VesselLogger

# ロガーの初期化
logger = VesselLogger(vessel_type="data")

def main():
    # コマンドライン引数からスクリプトを受け取る
    if len(sys.argv) < 2:
        logger.error("No script provided", usage="vessel_data_structured.py 'script'")
        sys.exit(1)
    
    script = ' '.join(sys.argv[1:])
    logger.debug(f"Script: {script}")
    
    # 標準入力から前段のデータを受け取る
    logger.debug("Reading data from stdin")
    input_data = sys.stdin.read().strip()
    logger.debug(f"Data length: {len(input_data)} chars")
    
    # 実行環境を準備（dataを自動的に注入）
    context = {
        '__name__': '__main__',
        'vessel': True,
        'data': input_data,
        'sys': sys,
        'json': __import__('json'),
        'print': logger.output  # print関数をラップ
    }
    
    # スクリプトを実行
    try:
        logger.debug("Executing script with data context")
        exec(script, context)
        logger.debug("Script execution completed")
    except Exception as e:
        logger.error("Script execution failed", error=e, script=script)
        sys.exit(1)

if __name__ == "__main__":
    main()