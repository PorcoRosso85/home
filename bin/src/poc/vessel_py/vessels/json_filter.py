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

def extract_path(data, path):
    """簡易的なJSONPath実装"""
    parts = path.strip('.').split('.')
    current = data
    
    for part in parts:
        if '[' in part:
            # 配列アクセス
            key, index = part.split('[')
            index = int(index.rstrip(']'))
            current = current[key][index]
        else:
            current = current[part]
    
    return current

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    data = json.loads(sys.stdin.read())
    
    try:
        result = extract_path(data, path)
        print(json.dumps(result))
    except (KeyError, IndexError, TypeError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)