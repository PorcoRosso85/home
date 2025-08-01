#!/usr/bin/env python3
"""
Data-aware Vessel - 前段の出力をdataとして受け取る器
"""
import sys

def main():
    # 標準入力から前段のデータを受け取る
    input_data = sys.stdin.read().strip()
    
    # 実行環境を準備（dataを自動的に注入）
    context = {
        '__name__': '__main__',
        'vessel': True,
        'data': input_data,  # 前段の出力をdataとして提供
        'sys': sys,
        'json': __import__('json'),
        'print': print
    }
    
    # コマンドライン引数からスクリプトを受け取る場合
    if len(sys.argv) > 1:
        script = ' '.join(sys.argv[1:])
    else:
        # スクリプトも標準入力から受け取る場合（区切り文字で分離）
        if '\n---SCRIPT---\n' in input_data:
            data_part, script = input_data.split('\n---SCRIPT---\n', 1)
            context['data'] = data_part.strip()
        else:
            # デフォルト：dataをそのまま出力
            script = 'print(data)'
    
    # スクリプトを実行
    try:
        exec(script, context)
    except Exception as e:
        print(f"Error executing script: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()