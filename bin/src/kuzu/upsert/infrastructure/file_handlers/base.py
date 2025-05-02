"""
ファイルハンドラーの基底クラスと型定義

ファイル読み込み処理の共通インターフェースを定義します。
"""

from typing import Dict, Any, Protocol, TypedDict, Optional, Union, Literal


class FileLoadSuccess(TypedDict):
    """ファイル読み込み成功結果"""
    data: Any
    file_name: str
    file_path: str
    file_size: int


class FileLoadError(TypedDict):
    """ファイル読み込みエラー"""
    code: str
    message: str
    file_path: str
    details: Dict[str, Any]


# 共用体型の定義
FileLoadResult = Union[FileLoadSuccess, FileLoadError]


class FileHandler(Protocol):
    """ファイルハンドラーのプロトコル

    各ファイル形式に対応したハンドラーはこのプロトコルに従って実装します。
    """
    @staticmethod
    def get_supported_extensions() -> list[str]:
        """サポートされているファイル拡張子のリストを取得
        
        Returns:
            list[str]: サポートされている拡張子のリスト（例: ['.yaml', '.yml']）
        """
        ...
    
    @staticmethod
    def load_file(file_path: str) -> FileLoadResult:
        """ファイルを読み込む
        
        Args:
            file_path: 読み込むファイルのパス
            
        Returns:
            FileLoadResult: 読み込み結果
        """
        ...


def create_file_load_success(data: Any, file_path: str, file_size: int) -> FileLoadSuccess:
    """ファイル読み込み成功結果を作成
    
    Args:
        data: 読み込んだデータ
        file_path: ファイルパス
        file_size: ファイルサイズ
        
    Returns:
        FileLoadSuccess: 成功結果
    """
    import os
    file_name = os.path.basename(file_path)
    
    return {
        "data": data,
        "file_name": file_name,
        "file_path": file_path,
        "file_size": file_size
    }


def create_file_load_error(code: str, message: str, file_path: str, details: Optional[Dict[str, Any]] = None) -> FileLoadError:
    """ファイル読み込みエラーを作成
    
    Args:
        code: エラーコード
        message: エラーメッセージ
        file_path: ファイルパス
        details: 詳細情報
        
    Returns:
        FileLoadError: エラー結果
    """
    return {
        "code": code,
        "message": message,
        "file_path": file_path,
        "details": details or {}
    }


def is_file_load_error(result: FileLoadResult) -> bool:
    """結果がエラーかどうかを判定
    
    Args:
        result: 判定する結果
        
    Returns:
        bool: エラーならTrue、そうでなければFalse
    """
    return "code" in result and "message" in result
