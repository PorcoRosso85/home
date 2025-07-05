#!/usr/bin/env python3
"""
Standalone search script - single file implementation for flake
"""

import os
import sys
import json
from pathlib import Path
from typing import Union, Optional, List, Literal, TypedDict
from urllib.parse import urlparse


# Type definitions
class SymbolDict(TypedDict):
    name: str
    type: Literal["function", "class", "method", "variable", "constant", "import", "type_alias"]
    path: str
    line: int
    column: Optional[int]
    context: Optional[str]


class MetadataDict(TypedDict):
    searched_files: int
    search_time_ms: float
    provider: Optional[str]


class SearchSuccessDict(TypedDict):
    symbols: List[SymbolDict]
    metadata: MetadataDict


class SearchErrorDict(TypedDict):
    error: str
    metadata: MetadataDict


SearchResult = Union[SearchSuccessDict, SearchErrorDict]


def search_symbols(path: str) -> SearchResult:
    """Search symbols in the given path"""
    # Noneや空文字列のチェック
    if not path:
        return SearchErrorDict(
            error="Path cannot be empty",
            metadata={"searched_files": 0, "search_time_ms": 0.0}
        )
    
    # URLスキーマの解析
    parsed = urlparse(path)
    
    # サポートされていないスキーマのチェック
    if parsed.scheme and parsed.scheme not in ["file", ""]:
        return SearchErrorDict(
            error=f"Unsupported scheme: {parsed.scheme}",
            metadata={"searched_files": 0, "search_time_ms": 0.0}
        )
    
    # file://スキーマの処理
    if parsed.scheme == "file":
        if parsed.netloc:
            local_path = parsed.path
        else:
            local_path = parsed.path
            if local_path.startswith("//"):
                local_path = local_path[2:]
            elif local_path.startswith("/") and os.name != 'posix':
                local_path = local_path[1:]
    else:
        local_path = path
    
    # パスの存在確認
    try:
        path_obj = Path(local_path).resolve()
        if not path_obj.exists():
            return SearchErrorDict(
                error=f"Path not found: {local_path}",
                metadata={"searched_files": 0, "search_time_ms": 0.0}
            )
    except Exception as e:
        return SearchErrorDict(
            error=str(e),
            metadata={"searched_files": 0, "search_time_ms": 0.0}
        )
    
    # シンボル収集
    symbols = []
    searched_files = 0
    
    try:
        if path_obj.is_file():
            if path_obj.suffix == ".py":
                symbols.extend(_extract_symbols_from_file(str(path_obj), parsed.scheme))
                searched_files = 1
        elif path_obj.is_dir():
            for py_file in path_obj.rglob("*.py"):
                symbols.extend(_extract_symbols_from_file(str(py_file), parsed.scheme))
                searched_files += 1
    except Exception as e:
        return SearchErrorDict(
            error=str(e),
            metadata={"searched_files": searched_files, "search_time_ms": 0.0}
        )
    
    return SearchSuccessDict(
        symbols=symbols,
        metadata={
            "searched_files": searched_files,
            "search_time_ms": 0.0
        }
    )


def _extract_symbols_from_file(file_path: str, url_scheme: str = "") -> List[SymbolDict]:
    """Extract symbols from a file"""
    symbols = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if url_scheme:
            display_path = f"{url_scheme}://{file_path}"
        else:
            display_path = file_path
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # クラス定義
            if stripped.startswith("class ") and ":" in stripped:
                name = stripped[6:].split("(")[0].split(":")[0].strip()
                if name:
                    symbols.append(SymbolDict(
                        name=name,
                        type="class",
                        path=display_path,
                        line=line_num,
                        column=None,
                        context=None
                    ))
            
            # 関数定義
            elif stripped.startswith("def ") and "(" in stripped:
                name = stripped[4:].split("(")[0].strip()
                if name:
                    symbol_type = "method" if line.startswith("    def ") else "function"
                    symbols.append(SymbolDict(
                        name=name,
                        type=symbol_type,
                        path=display_path,
                        line=line_num,
                        column=None,
                        context=None
                    ))
            
            # 変数/定数定義
            elif "=" in stripped and not stripped.startswith("#"):
                if not any(stripped.startswith(kw) for kw in ["import ", "from ", "if ", "elif ", "else"]):
                    parts = stripped.split("=", 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        if name and name.isidentifier():
                            symbol_type = "constant" if name.isupper() else "variable"
                            symbols.append(SymbolDict(
                                name=name,
                                type=symbol_type,
                                path=display_path,
                                line=line_num,
                                column=None,
                                context=None
                            ))
            
            # import文
            elif stripped.startswith("import ") or stripped.startswith("from "):
                symbols.append(SymbolDict(
                    name=stripped,
                    type="import",
                    path=display_path,
                    line=line_num,
                    column=None,
                    context=None
                ))
            
            # 型エイリアス
            elif "TypeAlias" in stripped or (": type[" in stripped or ": Type[" in stripped):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    if name and name.isidentifier():
                        symbols.append(SymbolDict(
                            name=name,
                            type="type_alias",
                            path=display_path,
                            line=line_num,
                            column=None,
                            context=None
                        ))
    
    except Exception:
        pass
    
    return symbols


def main():
    if len(sys.argv) < 2:
        print("Usage: search-symbols <path>", file=sys.stderr)
        sys.exit(1)
    
    result = search_symbols(sys.argv[1])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()