"""
シンボル検索の実装
bin/docs/conventions に従った最小限の実装
"""

import os
from pathlib import Path
from typing import Union
from urllib.parse import urlparse

try:
    from .types import SearchResult, SearchSuccessDict, SearchErrorDict, SymbolDict
except ImportError:
    from types import SearchResult, SearchSuccessDict, SearchErrorDict, SymbolDict


def search_symbols(path: str) -> SearchResult:
    """
    指定されたパスからシンボルを検索する
    
    Args:
        path: 検索対象のパス（ディレクトリ、ファイル、URLスキーマ）
    
    Returns:
        SearchSuccessDict | SearchErrorDict: 検索結果
    """
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
        # file:// を除去してローカルパスに変換
        # file://./path または file:///absolute/path を処理
        if parsed.netloc:
            # file://hostname/path の形式（localhostなど）
            local_path = parsed.path
        else:
            # file:///path または file://path の形式
            local_path = parsed.path
            if local_path.startswith("//"):
                local_path = local_path[2:]
            elif local_path.startswith("/") and os.name != 'posix':
                # Windowsでの絶対パス処理
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
            # 単一ファイルの処理
            if path_obj.suffix == ".py":
                symbols.extend(_extract_symbols_from_file(str(path_obj), parsed.scheme))
                searched_files = 1
        elif path_obj.is_dir():
            # ディレクトリの処理
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
            "search_time_ms": 0.0  # 簡易実装のため0.0
        }
    )


def _extract_symbols_from_file(file_path: str, url_scheme: str = "") -> list[SymbolDict]:
    """
    ファイルからシンボルを抽出する（最小限の実装）
    """
    symbols = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # URLスキーマ付きのパスを生成
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
                    # インデントレベルでメソッドか関数か判定
                    symbol_type = "method" if line.startswith("    def ") else "function"
                    symbols.append(SymbolDict(
                        name=name,
                        type=symbol_type,
                        path=display_path,
                        line=line_num,
                        column=None,
                        context=None
                    ))
            
            # 変数/定数定義（簡易的な判定）
            elif "=" in stripped and not stripped.startswith("#"):
                # importやifなどは除外
                if not any(stripped.startswith(kw) for kw in ["import ", "from ", "if ", "elif ", "else"]):
                    parts = stripped.split("=", 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        if name and name.isidentifier():
                            # 大文字のみなら定数
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
            
            # 型エイリアス（TypeAliasを含む行）
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
        # ファイル読み取りエラーは無視して空のリストを返す
        pass
    
    return symbols