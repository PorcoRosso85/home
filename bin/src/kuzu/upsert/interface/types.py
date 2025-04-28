"""
インターフェースレイヤーの型定義

このモジュールでは、CLIインターフェースで使用する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Literal, Any, Dict, Tuple, Callable


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


class SHACLValidationSuccess(TypedDict):
    """SHACL検証成功"""
    is_valid: Literal[True]
    report: str
    details: Dict[str, Any]


class SHACLValidationFailure(TypedDict):
    """SHACL検証失敗"""
    is_valid: Literal[False]
    report: str
    details: SHACLValidationDetails
    error_type: str  # エラータイプ (shacl_violation, validation_error, etc.)


class SHACLValidationError(TypedDict):
    """SHACL検証エラー"""
    code: str
    message: str


SHACLValidationResult = Union[SHACLValidationSuccess, SHACLValidationFailure, SHACLValidationError]


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


# エラーハンドリング関連の型
class CommandError(TypedDict):
    """コマンド実行エラー"""
    success: Literal[False]
    command: str  # エラーが発生したコマンド
    error_type: str  # エラータイプ
    message: str  # エラーメッセージ
    trace: Optional[str]  # スタックトレース（デバッグモードでのみ使用）


class CommandSuccess(TypedDict):
    """コマンド実行成功"""
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
    return isinstance(result, dict) and "code" in result and "message" in result


# テスト関数
def test_is_error() -> None:
    """is_error関数のテスト"""
    # エラーの場合
    error_result: FunctionError = {"code": "TEST_ERROR", "message": "テストエラー"}
    assert is_error(error_result) is True
    
    # 正常データの場合
    success_result: FunctionData = {
        "title": "TestFunction",
        "description": "Test description",
        "type": "function",
        "pure": True,
        "async_value": False,
        "parameters": {},
        "returnType": {}
    }
    assert is_error(success_result) is False
    
    # 不正なデータの場合
    assert is_error(None) is False
    assert is_error("string") is False
    assert is_error(123) is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
