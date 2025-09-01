#!/usr/bin/env python3
"""Find all module.json files in a project."""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def find_module_files(root_path: str, exclude_dirs: List[str] = None) -> List[Path]:
    """Find all module.json files under root_path."""
    if exclude_dirs is None:
        exclude_dirs = ['.git', 'node_modules', '__pycache__', '.nix', 'dist', 'build']
    
    root = Path(root_path)
    if not root.exists():
        print(f"Error: Path {root_path} does not exist")
        sys.exit(1)
    
    module_files = []
    for path in root.rglob('module.json'):
        # Skip excluded directories
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        module_files.append(path)
    
    return module_files


def load_module(file_path: Path) -> Dict[str, Any]:
    """Load and parse a module.json file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <root_path>")
        sys.exit(1)
    
    root_path = sys.argv[1]
    module_files = find_module_files(root_path)
    
    print(f"Found {len(module_files)} module.json files:")
    
    for file_path in module_files:
        module = load_module(file_path)
        if module:
            module_id = module.get('id', 'unknown')
            module_type = module.get('type', 'unknown')
            print(f"  {file_path.parent}: {module_id} ({module_type})")


if __name__ == "__main__":
    main()