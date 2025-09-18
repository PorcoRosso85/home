#!/usr/bin/env python3
"""
ctags-based path finder
指定したシンボルのファイルパスと行番号を返す
"""

import subprocess
import sys
import json
from typing import List, Dict, Optional
from pathlib import Path
import tempfile
import argparse


def generate_ctags(directory: str, extensions: List[str]) -> str:
    """指定ディレクトリのctagsを生成"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tags', delete=False) as f:
        tags_file = f.name
    
    # ctags コマンドを構築
    cmd = ['ctags', '-f', tags_file, '-R', '--fields=+n']
    
    # 言語指定
    if extensions:
        for ext in extensions:
            cmd.extend([f'--langmap=python:+.{ext}'])
    
    cmd.append(directory)
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return tags_file
    except subprocess.CalledProcessError as e:
        print(f"Error generating ctags: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def parse_ctags_line(line: str) -> Optional[Dict[str, str]]:
    """ctagsの行をパース"""
    parts = line.strip().split('\t')
    if len(parts) < 4:
        return None
    
    symbol = parts[0]
    file_path = parts[1]
    
    # 行番号を探す
    line_num = None
    for field in parts[3:]:
        if field.startswith('line:'):
            line_num = field.split(':')[1]
            break
    
    # タイプを判定
    ex_cmd = parts[2]
    symbol_type = 'unknown'
    if 'class ' in ex_cmd:
        symbol_type = 'class'
    elif 'def ' in ex_cmd:
        symbol_type = 'function'
    
    return {
        'name': symbol,
        'file': file_path,
        'line': int(line_num) if line_num else 0,
        'type': symbol_type
    }


def find_symbols(tags_file: str, pattern: str = None) -> List[Dict[str, str]]:
    """tagsファイルからシンボルを検索"""
    symbols = []
    
    with open(tags_file, 'r') as f:
        for line in f:
            if line.startswith('!'):  # コメント行をスキップ
                continue
            
            parsed = parse_ctags_line(line)
            if parsed:
                if pattern is None or pattern in parsed['name']:
                    symbols.append(parsed)
    
    return sorted(symbols, key=lambda x: (x['file'], x['line']))


def main():
    parser = argparse.ArgumentParser(description='Find symbols using ctags')
    parser.add_argument('directory', help='Directory to search')
    parser.add_argument('--pattern', '-p', help='Symbol pattern to search')
    parser.add_argument('--ext', '-e', action='append', help='File extensions (can be repeated)')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # デフォルト拡張子
    extensions = args.ext or ['py']
    
    # ctagsを生成
    tags_file = generate_ctags(args.directory, extensions)
    
    try:
        # シンボルを検索
        symbols = find_symbols(tags_file, args.pattern)
        
        if args.json:
            print(json.dumps(symbols, indent=2))
        else:
            for sym in symbols:
                print(f"{sym['name']:<30} {sym['type']:<10} {sym['file']}:{sym['line']}")
    finally:
        # 一時ファイルを削除
        Path(tags_file).unlink(missing_ok=True)


if __name__ == '__main__':
    main()