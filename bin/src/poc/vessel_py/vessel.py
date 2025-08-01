#!/usr/bin/env python3
"""
Vessel - 動的スクリプト実行コンテナ
標準入力から受け取ったPythonコードを実行する器
"""
import sys

def main():
    # 標準入力からスクリプトを読み込む
    script = sys.stdin.read()
    
    # 実行環境を準備
    context = {
        '__name__': '__main__',
        'vessel': True  # vessel内で実行されていることを示すフラグ
    }
    
    # スクリプトを実行
    try:
        exec(script, context)
    except Exception as e:
        print(f"Error executing script: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()