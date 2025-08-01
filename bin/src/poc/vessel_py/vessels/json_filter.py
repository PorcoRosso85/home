#!/usr/bin/env python3
"""
@vessel
@category: transform
@tags: json,filter,extract
@input: json
@output: json
@description: JSONから指定フィールドを抽出
@examples:
  - input: {"users": [{"name": "Alice"}]}
    args: .users[0].name
    output: "Alice"
"""
import sys
import json
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vessel_log import VesselLogger

def extract_path(data, path):
    """簡易的なJSONPath実装"""
    if path == ".":
        return data
    
    parts = path.strip('.').split('.')
    current = data
    
    for part in parts:
        if not part:  # Skip empty parts
            continue
        if '[' in part:
            # 配列アクセス
            key, index = part.split('[')
            index = int(index.rstrip(']'))
            current = current[key][index]
        else:
            current = current[part]
    
    return current

if __name__ == "__main__":
    logger = VesselLogger("json_filter")
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        logger.error("Failed to parse input JSON", error=e)
        sys.exit(1)
    
    try:
        result = extract_path(data, path)
        # Normal output stays as print to maintain vessel output contract
        print(json.dumps(result))
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to extract path '{path}'", error=e, path=path)
        sys.exit(1)