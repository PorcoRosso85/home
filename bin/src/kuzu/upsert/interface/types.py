"""
インターフェースレイヤーの型定義

このモジュールでは、CLIインターフェースで使用する型定義を行います。
統一されたエラーハンドリング規約に準拠した型定義も含まれています。
"""

from typing import TypedDict, Union, List, Optional, Literal, Any, Dict, Tuple, Callable, Set
from enum import Enum, auto


# データベース関連の型
class DatabaseConnection(TypedDict):
    """データベース接続情報"""
    connection: Any  # Kuzuのコネクション型


class DatabaseError(TypedDict):
    """データベース操作エラー"""
    code: str
    message: str


DatabaseResult = Union[DatabaseConnection, DatabaseError]


# SHACL検証結果の型
class ValidationSuccess(TypedDict):
    """検証成功結果"""
    is_valid: Literal[True]
    report: str


class ValidationFailure(TypedDict):
    """検証失敗結果"""
    is_valid: Literal[False]
    report: str


class ValidationError(TypedDict):
    """検証エラー"""
    code: str
    message: str


ValidationResult = Union[ValidationSuccess, ValidationFailure, ValidationError]


# SHACL検証結果の詳細型
class SHACLConstraintViolation(TypedDict):
    """SHACL制約違反情報"""
    type: str  # エラータイプ (missing_required_property, invalid_property_value, etc.)
    property: Optional[str]  # プロパティ名
    value: Optional[str]  # 違反値
    node_type: Optional[str]  # ノードタイプ
    description: str  # 説明
    suggestion: str  # 修正提案


class SHACLValidationDetails(TypedDict):
    """SHACL検証詳細"""
    violations: List[SHACLConstraintViolation]  # 違反リスト
    suggestions: List[str]  # 修正提案リスト
    query_pattern: Optional[str]  # クエリパターン
    summary: str  # 要約


# SHACL検証型は domain.validation.types に移動しました
from upsert.domain.validation.types import (
    SHACLValidationSuccess,
    SHACLValidationFailure,
    SHACLValidationError,
    SHACLValidationResult,
)


# クエリ検証と補完の拡張型
class SHACLViolationDisplay(TypedDict):
    """SHACL制約違反表示用データ"""
    message: str  # 表示メッセージ
    property: Optional[str]  # プロパティ名
    suggestion: str  # 修正提案
    severity: Literal["error", "warning", "info"]  # 重要度


class SHACLFeedback(TypedDict):
    """SHACL検証フィードバック"""
    is_valid: bool  # 検証結果
    message: str  # 全体メッセージ
    violations: List[SHACLViolationDisplay]  # 違反リスト
    suggestions: List[str]  # 修正提案リスト


# クエリ補完とサジェスト関連の型
class QuerySuggestionItem(TypedDict):
    """クエリ補完候補アイテム"""
    type: str  # keyword, pattern, node_label, property, relationship, etc.
    value: str  # 補完テキスト
    description: str  # 説明
    priority: Optional[int]  # 表示優先度（高いほど上に表示）
    example: Optional[str]  # 使用例


class SHACLConstraintInfo(TypedDict):
    """SHACL制約情報"""
    required_properties: List[str]  # 必須プロパティ
    type_values: Dict[str, str]  # 特定の値が必要なプロパティ
    examples: str  # 例文


class QueryConstraints(TypedDict):
    """クエリ制約情報"""
    node_requirements: Dict[str, SHACLConstraintInfo]  # ノードタイプごとの制約
    relationship_requirements: Dict[str, Any]  # 関係タイプごとの制約
    hint: str  # ヒントメッセージ


class QueryContext(TypedDict):
    """クエリコンテキスト情報"""
    stage: str  # start, node_selection, query_continuation, etc.
    message: str  # コンテキストメッセージ
    query_type: Optional[str]  # match, create, set, etc.
    current_labels: List[str]  # 現在使用されているラベル
    current_properties: List[str]  # 現在使用されているプロパティ


class SuggestionResult(TypedDict):
    """サジェスト結果"""
    success: bool  # 成功フラグ
    message: str  # メッセージ
    suggestions: List[QuerySuggestionItem]  # 補完候補
    context: Optional[QueryContext]  # クエリコンテキスト


class QueryCompletionResult(TypedDict):
    """クエリ補完結果"""
    success: bool  # 成功フラグ
    completions: List[QuerySuggestionItem]  # 補完候補
    context: QueryContext  # クエリコンテキスト
    analysis: Dict[str, Any]  # クエリ解析結果


class QuerySuggestionResult(TypedDict):
    """クエリサジェスト結果"""
    success: bool  # 成功フラグ
    message: str  # メッセージ
    suggestions: List[QuerySuggestionItem]  # 補完候補
    constraints: Optional[QueryConstraints]  # 制約情報
    analysis: Optional[Dict[str, Any]]  # 解析情報


class QueryInput(TypedDict):
    """クエリ入力データ"""
    query: str  # クエリ文字列
    param_strings: Optional[List[str]]  # パラメータ文字列リスト
    interactive: bool  # インタラクティブモード
    with_suggestions: bool  # 候補表示あり


class QueryAnalysisResult(TypedDict):
    """クエリ解析結果"""
    success: bool  # 成功フラグ
    query_type: str  # match, create, set, etc.
    commands: List[str]  # コマンドリスト
    patterns: Dict[str, Tuple]  # 検出パターン
    node_types: List[str]  # ノードタイプ
    relationship_types: List[str]  # 関係タイプ
    property_references: List[Tuple[str, str]]  # プロパティ参照


class QueryExecutionResult(TypedDict):
    """クエリ実行結果"""
    success: bool  # 成功フラグ
    data: Any  # 結果データ
    stats: Dict[str, Any]  # 統計情報
    message: Optional[str]  # メッセージ (エラー時)


class QueryOutput(TypedDict):
    """クエリ出力データ"""
    success: bool  # 成功フラグ
    message: str  # メッセージ
    validation: SHACLFeedback  # 検証結果
    execution: QueryExecutionResult  # 実行結果
    suggestions: Optional[List[QuerySuggestionItem]]  # 補完候補
    analysis: Optional[QueryAnalysisResult]  # 解析結果


class QueryValidationResult(TypedDict):
    """クエリ検証結果"""
    validation: SHACLValidationResult  # SHACL検証結果
    execution: QueryExecutionResult  # 実行結果
    suggestions: Optional[QuerySuggestionResult]  # サジェスト結果
    help: Optional[Dict[str, Any]]  # ヘルプ情報
    analysis: Optional[QueryAnalysisResult]  # 解析結果


class QueryHelpResult(TypedDict):
    """クエリヘルプ結果"""
    success: bool  # 成功フラグ
    help: Dict[str, Any]  # ヘルプ情報


class QueryPattern(TypedDict):
    """クエリパターン情報"""
    type: str  # match, create, set, etc.
    node_labels: List[str]  # ノードラベル
    relationships: List[str]  # 関係タイプ
    properties: List[str]  # プロパティ
    example: str  # 例文


class QueryPatternList(TypedDict):
    """クエリパターン一覧"""
    patterns: List[QueryPattern]
    categories: List[str]  # カテゴリリスト


class InteractiveModeOptions(TypedDict):
    """インタラクティブモードオプション"""
    show_constraints: bool  # 制約情報を表示
    show_suggestions: bool  # 候補を表示
    show_validation: bool  # 検証結果を表示
    auto_complete: bool  # 自動補完


# 関数データの型
class FunctionData(TypedDict):
    """関数データ"""
    title: str
    description: Optional[str]
    type: str
    pure: bool
    async_value: bool
    parameters: Dict[str, Any]
    returnType: Dict[str, Any]


class FunctionError(TypedDict):
    """関数操作エラー"""
    code: str
    message: str


FunctionResult = Union[FunctionData, FunctionError]


# 関数一覧の型
class FunctionListItem(TypedDict):
    """関数一覧項目"""
    title: str
    description: Optional[str]
    type: str


class FunctionList(TypedDict):
    """関数一覧"""
    functions: List[FunctionListItem]


FunctionListResult = Union[FunctionList, FunctionError]


# ファイル操作の型
class FileContent(TypedDict):
    """ファイル内容"""
    data: Any


class FileError(TypedDict):
    """ファイル操作エラー"""
    code: str
    message: str


FileResult = Union[FileContent, FileError]


# RDF生成の型
class RDFContent(TypedDict):
    """RDF内容"""
    data: str


RDFResult = Union[RDFContent, FileError]


# コマンドライン引数の型
class CommandArgs(TypedDict, total=False):
    """コマンドライン引数"""
    init: bool
    add: Optional[str]
    list: bool
    get: Optional[str]
    init_convention: Optional[str]
    create_shapes: bool
    test: bool
    query: Optional[str]
    param: Optional[List[str]]
    help_query: Optional[str]
    show_examples: Optional[str]
    interactive: bool
    suggest: Optional[str]
    debug: bool  # デバッグモードで実行するかどうか
    verbose: bool  # 詳細表示モードで実行するかどうか


# 統一されたエラーコード
class ErrorCode(str, Enum):
    """共通エラーコード"""
    # 一般的なエラー
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    MISSING_REQUIRED_ARGUMENT = "MISSING_REQUIRED_ARGUMENT"
    UNKNOWN_COMMAND = "UNKNOWN_COMMAND"
    INVALID_FORMAT = "INVALID_FORMAT"
    NOT_FOUND = "NOT_FOUND"
    
    # データベース関連のエラー
    DB_CONNECTION_ERROR = "DB_CONNECTION_ERROR"
    DB_QUERY_ERROR = "DB_QUERY_ERROR"
    DB_INIT_ERROR = "DB_INIT_ERROR"
    DB_PATH_ERROR = "DB_PATH_ERROR"
    
    # クエリ関連のエラー
    QUERY_SYNTAX_ERROR = "QUERY_SYNTAX_ERROR"
    QUERY_VALIDATION_ERROR = "QUERY_VALIDATION_ERROR"
    QUERY_EXECUTION_ERROR = "QUERY_EXECUTION_ERROR"
    PARAM_PARSE_ERROR = "PARAM_PARSE_ERROR"
    
    # ファイル操作関連のエラー
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_ERROR = "FILE_ACCESS_ERROR"
    FILE_PARSE_ERROR = "FILE_PARSE_ERROR"
    
    # データ操作関連のエラー
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    SHACL_VALIDATION_ERROR = "SHACL_VALIDATION_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    
    # その他のエラー
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


# 標準化されたエラーメッセージマッピング
ERROR_MESSAGES = {
    ErrorCode.INVALID_ARGUMENT: "無効な引数が指定されました",
    ErrorCode.MISSING_REQUIRED_ARGUMENT: "必須の引数が不足しています",
    ErrorCode.UNKNOWN_COMMAND: "不明なコマンドが指定されました",
    ErrorCode.INVALID_FORMAT: "無効なデータ形式です",
    ErrorCode.NOT_FOUND: "指定されたリソースが見つかりません",
    
    ErrorCode.DB_CONNECTION_ERROR: "データベース接続に失敗しました",
    ErrorCode.DB_QUERY_ERROR: "データベースクエリの実行に失敗しました",
    ErrorCode.DB_INIT_ERROR: "データベースの初期化に失敗しました",
    ErrorCode.DB_PATH_ERROR: "データベースパスの指定に問題があります",
    
    ErrorCode.QUERY_SYNTAX_ERROR: "クエリの構文にエラーがあります",
    ErrorCode.QUERY_VALIDATION_ERROR: "クエリの検証に失敗しました",
    ErrorCode.QUERY_EXECUTION_ERROR: "クエリの実行中にエラーが発生しました",
    ErrorCode.PARAM_PARSE_ERROR: "パラメータの解析に失敗しました",
    
    ErrorCode.FILE_NOT_FOUND: "ファイルが見つかりません",
    ErrorCode.FILE_ACCESS_ERROR: "ファイルへのアクセスに失敗しました",
    ErrorCode.FILE_PARSE_ERROR: "ファイルの解析に失敗しました",
    
    ErrorCode.DATA_VALIDATION_ERROR: "データ検証に失敗しました",
    ErrorCode.SHACL_VALIDATION_ERROR: "SHACL検証エラーが発生しました",
    ErrorCode.SCHEMA_ERROR: "スキーマエラーが発生しました",
    
    ErrorCode.UNEXPECTED_ERROR: "予期しないエラーが発生しました",
    ErrorCode.NOT_IMPLEMENTED: "この機能は実装されていません"
}


# 基本エラー型
class BaseError(TypedDict):
    """基本エラー型"""
    code: str
    message: str
    details: Optional[Dict[str, Any]]


# コマンド別エラー型
class InitError(TypedDict):
    """初期化コマンドエラー"""
    error_type: Literal["DB_PATH_ERROR", "DB_INIT_ERROR", "VALIDATION_ERROR", "INIT_DATA_ERROR"]
    message: str
    details: Dict[str, Any]


class QueryError(TypedDict):
    """クエリコマンドエラー"""
    error_type: Literal["QUERY_SYNTAX_ERROR", "QUERY_VALIDATION_ERROR", "QUERY_EXECUTION_ERROR", "PARAM_PARSE_ERROR"]
    message: str
    details: Dict[str, Any]


class GetError(TypedDict):
    """取得コマンドエラー"""
    error_type: Literal["NOT_FOUND", "DB_CONNECTION_ERROR", "INVALID_ARGUMENT"]
    message: str
    details: Dict[str, Any]


# コマンド実行結果型
class CommandError(TypedDict):
    """コマンド実行エラー（統一形式）"""
    success: Literal[False]
    command: str  # エラーが発生したコマンド
    error_type: str  # エラータイプ（ErrorCode列挙型の値）
    message: str  # エラーメッセージ
    details: Optional[Dict[str, Any]]  # 詳細情報（エラーに応じた追加データ）
    trace: Optional[str]  # スタックトレース（デバッグモードでのみ使用）


class CommandSuccess(TypedDict):
    """コマンド実行成功（統一形式）"""
    success: Literal[True]
    message: str  # 成功メッセージ
    data: Optional[Dict[str, Any]]  # コマンド固有のデータ


CommandResult = Union[CommandSuccess, CommandError]


class CommandInfo(TypedDict):
    """コマンド情報"""
    name: str  # コマンド名
    description: str  # コマンドの説明
    usage: str  # 使用方法
    examples: List[str]  # 使用例
    handler: Callable  # コマンドハンドラー関数


# ヘルパー関数
def is_error(result: Any) -> bool:
    """結果がエラーかどうかを判定する
    
    Args:
        result: 判定対象の結果

    Returns:
        bool: エラーならTrue、それ以外はFalse
    """
    # 基本的なエラー型チェック
    if isinstance(result, dict):
        # 統一された形式のエラー判定
        if "code" in result and "message" in result:
            return True
        
        # コマンドエラー型の判定
        if "success" in result and result.get("success") is False and "error_type" in result:
            return True
        
        # コマンド固有エラー型の判定
        if "error_type" in result and "message" in result and "details" in result:
            return True
    
    return False


def get_error_code(result: Any) -> Optional[str]:
    """エラーからエラーコードを取得する
    
    Args:
        result: 判定対象の結果

    Returns:
        Optional[str]: エラーコード。エラーでない場合はNone
    """
    if not is_error(result):
        return None
    
    if isinstance(result, dict):
        if "code" in result:
            return result["code"]
        elif "error_type" in result:
            return result["error_type"]
    
    return None


def get_error_message(result: Any) -> Optional[str]:
    """エラーからエラーメッセージを取得する
    
    Args:
        result: 判定対象の結果

    Returns:
        Optional[str]: エラーメッセージ。エラーでない場合はNone
    """
    if not is_error(result):
        return None
    
    if isinstance(result, dict) and "message" in result:
        return result["message"]
    
    return None


def create_error(code: str, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> BaseError:
    """統一されたエラーを作成する
    
    Args:
        code: エラーコード
        message: エラーメッセージ。指定しない場合はコードに対応する標準メッセージ
        details: 詳細情報

    Returns:
        BaseError: 作成されたエラー
    """
    if message is None:
        # ErrorCode列挙型の値であればマッピングからメッセージを取得
        if code in ERROR_MESSAGES:
            message = ERROR_MESSAGES[code]
        else:
            message = f"エラーが発生しました: {code}"
    
    return {
        "code": code,
        "message": message,
        "details": details
    }


def create_command_error(
    command: str,
    error_type: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    trace: Optional[str] = None
) -> CommandError:
    """コマンドエラーを作成する
    
    Args:
        command: エラーが発生したコマンド名
        error_type: エラータイプ
        message: エラーメッセージ
        details: 詳細情報
        trace: スタックトレース

    Returns:
        CommandError: 作成されたコマンドエラー
    """
    if message is None:
        # エラータイプに対応する標準メッセージを取得
        if error_type in ERROR_MESSAGES:
            message = ERROR_MESSAGES[error_type]
        else:
            message = f"コマンド {command} でエラーが発生しました: {error_type}"
    
    return {
        "success": False,
        "command": command,
        "error_type": error_type,
        "message": message,
        "details": details,
        "trace": trace
    }


def create_command_success(
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> CommandSuccess:
    """コマンド成功結果を作成する
    
    Args:
        message: 成功メッセージ
        data: コマンド固有のデータ

    Returns:
        CommandSuccess: 作成されたコマンド成功結果
    """
    return {
        "success": True,
        "message": message,
        "data": data
    }


# テスト関数
def test_is_error() -> None:
    """統一されたエラー判別関数のテスト"""
    # 基本エラー型
    base_error: BaseError = {
        "code": "TEST_ERROR",
        "message": "テストエラー",
        "details": None
    }
    assert is_error(base_error) is True
    
    # 古い形式のエラー
    old_error: FunctionError = {
        "code": "TEST_ERROR",
        "message": "テストエラー"
    }
    assert is_error(old_error) is True
    
    # コマンドエラー
    command_error: CommandError = {
        "success": False,
        "command": "test",
        "error_type": "TEST_ERROR",
        "message": "テストエラー",
        "details": None,
        "trace": None
    }
    assert is_error(command_error) is True
    
    # コマンド固有エラー
    init_error: InitError = {
        "error_type": "DB_PATH_ERROR",
        "message": "データベースパスが無効です",
        "details": {"path": "/invalid/path"}
    }
    assert is_error(init_error) is True
    
    # 成功結果
    success_result: CommandSuccess = {
        "success": True,
        "message": "成功しました",
        "data": None
    }
    assert is_error(success_result) is False
    
    # 通常のデータ
    function_data: FunctionData = {
        "title": "TestFunction",
        "description": "Test description",
        "type": "function",
        "pure": True,
        "async_value": False,
        "parameters": {},
        "returnType": {}
    }
    assert is_error(function_data) is False
    
    # 不正なデータ
    assert is_error(None) is False
    assert is_error("string") is False
    assert is_error(123) is False


def test_error_creation() -> None:
    """エラー作成関数のテスト"""
    # 基本エラー作成
    error = create_error(ErrorCode.INVALID_ARGUMENT)
    assert error["code"] == ErrorCode.INVALID_ARGUMENT
    assert error["message"] == ERROR_MESSAGES[ErrorCode.INVALID_ARGUMENT]
    assert error["details"] is None
    
    # カスタムメッセージでエラー作成
    custom_message = "カスタムエラーメッセージ"
    error = create_error(ErrorCode.NOT_FOUND, custom_message)
    assert error["code"] == ErrorCode.NOT_FOUND
    assert error["message"] == custom_message
    
    # 詳細情報付きエラー作成
    details = {"param": "test", "value": 123}
    error = create_error(ErrorCode.INVALID_ARGUMENT, None, details)
    assert error["code"] == ErrorCode.INVALID_ARGUMENT
    assert error["details"] == details
    
    # コマンドエラー作成
    cmd_error = create_command_error("test", ErrorCode.DB_CONNECTION_ERROR)
    assert cmd_error["success"] is False
    assert cmd_error["command"] == "test"
    assert cmd_error["error_type"] == ErrorCode.DB_CONNECTION_ERROR
    assert cmd_error["message"] == ERROR_MESSAGES[ErrorCode.DB_CONNECTION_ERROR]
    
    # コマンド成功結果作成
    cmd_success = create_command_success("テスト成功")
    assert cmd_success["success"] is True
    assert cmd_success["message"] == "テスト成功"
    assert cmd_success["data"] is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
