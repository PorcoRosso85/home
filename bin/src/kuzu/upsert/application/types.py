"""
アプリケーションレイヤーの型定義

このモジュールでは、アプリケーションサービスで使用する型定義を行います。
"""

from typing import TypedDict, Union, List, Optional, Dict, Any, Literal, Callable, Set, Tuple


# データベース関連の型
class DatabaseConnection(TypedDict):
    """データベース接続情報"""
    connection: Any  # Kuzuのコネクション型


class DatabaseError(TypedDict):
    """データベース操作エラー"""
    code: str
    message: str


DatabaseResult = Union[DatabaseConnection, DatabaseError]


# データベース初期化サービスの型
class DatabaseInitializationSuccess(TypedDict):
    """データベース初期化成功結果"""
    message: str
    connection: Any


class DatabaseInitializationError(TypedDict):
    """データベース初期化エラー"""
    code: str
    message: str


DatabaseInitializationResult = Union[DatabaseInitializationSuccess, DatabaseInitializationError]


# SHACL検証サービスの型
class SHACLValidationSuccess(TypedDict):
    """SHACL検証成功結果"""
    is_valid: Literal[True]
    report: str


class SHACLValidationFailure(TypedDict):
    """SHACL検証失敗結果"""
    is_valid: Literal[False]
    report: str


class SHACLValidationError(TypedDict):
    """SHACL検証エラー（例：ファイルが見つからないなど）"""
    code: str
    message: str


SHACLValidationResult = Union[SHACLValidationSuccess, SHACLValidationFailure, SHACLValidationError]


# SHACLエラーと制約に関する拡張型定義
class SHACLErrorViolation(TypedDict):
    """SHACL制約違反情報"""
    type: str  # エラータイプ: missing_required_property, invalid_property_value, etc.
    message: str  # エラーメッセージ
    description: str  # 人間向けの説明文
    suggestion: Optional[str]  # 修正提案
    property: Optional[str]  # 違反しているプロパティ名
    node_type: Optional[str]  # ノードタイプ
    value: Optional[str]  # 違反している値


class SHACLErrorAnalysisDetected(TypedDict):
    """検出されたSHACL制約違反情報"""
    error_type: Literal["detected"]
    violations: List[SHACLErrorViolation]  # 検出された違反リスト
    errors: List[SHACLErrorViolation]  # 古い API 互換用
    original_message: str  # 元のエラーメッセージ
    query_pattern: Optional[str]  # クエリパターン(match, create, set, etc.)
    summary: str  # 要約メッセージ
    suggestions: List[str]  # 修正提案のリスト
    node_types: Optional[List[str]]  # 関連するノードタイプ


class SHACLErrorAnalysisUnknown(TypedDict):
    """未検出のSHACL制約違反情報"""
    error_type: Literal["unknown"]
    description: str  # エラーの説明
    original_message: str  # 元のエラーメッセージ
    query_pattern: Optional[str]  # クエリパターン
    suggestions: List[str]  # 一般的な修正提案のリスト


SHACLErrorAnalysisResult = Union[SHACLErrorAnalysisDetected, SHACLErrorAnalysisUnknown]


# SHACL制約情報の型
class SHACLNodeRequirement(TypedDict):
    """ノードタイプごとのSHACL制約要件"""
    required_properties: List[str]  # 必須プロパティ
    type_values: Optional[Dict[str, str]]  # プロパティ名と期待値のマッピング
    examples: Optional[str]  # 例文


class SHACLRelationshipRequirement(TypedDict):
    """関係タイプごとのSHACL制約要件"""
    source_node: str  # ソースノードタイプ
    target_node: str  # ターゲットノードタイプ
    examples: Optional[str]  # 例文


class SHACLConstraintInfo(TypedDict):
    """SHACL制約情報"""
    node_requirements: Dict[str, SHACLNodeRequirement]  # ノードタイプごとの要件
    relationship_requirements: Dict[str, SHACLRelationshipRequirement]  # 関係タイプごとの要件
    hint: str  # ヒントメッセージ


# クエリ解析結果の型
class QueryPatternAnalysis(TypedDict):
    """クエリパターン解析結果"""
    success: bool
    query_type: str  # MATCH, CREATE, SET, etc.
    commands: List[str]  # 含まれるコマンド
    patterns: Dict[str, Any]  # 検出されたパターン
    node_types: List[str]  # 含まれるノードタイプ
    relationship_types: List[str]  # 含まれる関係タイプ
    property_references: List[Tuple[str, str]]  # 参照されているプロパティ


# 関数型サービスの型
class FunctionTypeCreationSuccess(TypedDict):
    """関数型作成成功結果"""
    title: str
    description: Optional[str]
    message: str


class FunctionTypeCreationError(TypedDict):
    """関数型作成エラー"""
    code: str
    message: str


FunctionTypeCreationResult = Union[FunctionTypeCreationSuccess, FunctionTypeCreationError]


# 関数型取得サービスの型
class FunctionTypeData(TypedDict):
    """関数型データ"""
    title: str
    description: Optional[str]
    type: str
    pure: bool
    async_value: bool
    parameters: Dict[str, Any]
    returnType: Dict[str, Any]


class FunctionTypeQueryError(TypedDict):
    """関数型検索エラー"""
    code: str
    message: str


FunctionTypeQueryResult = Union[FunctionTypeData, FunctionTypeQueryError]


# 関数型一覧取得サービスの型
class FunctionTypeListItem(TypedDict):
    """関数型一覧項目"""
    title: str
    description: Optional[str]


class FunctionTypeList(TypedDict):
    """関数型一覧"""
    functions: List[FunctionTypeListItem]


FunctionTypeListResult = Union[FunctionTypeList, FunctionTypeQueryError]


# RDF変換サービスの型
class RDFGenerationSuccess(TypedDict):
    """RDF生成成功結果"""
    content: str


class RDFGenerationError(TypedDict):
    """RDF生成エラー"""
    code: str
    message: str


RDFGenerationResult = Union[RDFGenerationSuccess, RDFGenerationError]


# ファイル操作サービスの型
class FileOperationSuccess(TypedDict):
    """ファイル操作成功結果"""
    path: str
    message: str


class FileOperationError(TypedDict):
    """ファイル操作エラー"""
    code: str
    message: str


FileOperationResult = Union[FileOperationSuccess, FileOperationError]


# クエリローダーサービスの型
class QueryLoaderSuccess(TypedDict):
    """クエリローダー成功結果"""
    connection: Any  # DB接続
    query_loader: Dict[str, Callable]  # クエリローダー


class QueryLoaderError(TypedDict):
    """クエリローダーエラー"""
    code: str
    message: str


QueryLoaderResult = Union[QueryLoaderSuccess, QueryLoaderError]


class QueryExecutionSuccess(TypedDict):
    """クエリ実行成功結果"""
    data: Any


class QueryExecutionError(TypedDict):
    """クエリ実行エラー"""
    code: str
    message: str


QueryExecutionResult = Union[QueryExecutionSuccess, QueryExecutionError]


# クエリ検証結果の型
class QueryValidationSuccess(TypedDict):
    """クエリ検証成功結果"""
    is_valid: Literal[True]
    report: str
    details: Dict[str, Any]


class QueryValidationFailure(TypedDict):
    """クエリ検証失敗結果"""
    is_valid: Literal[False]
    report: str
    details: Dict[str, Any]


QueryValidationResult = Union[QueryValidationSuccess, QueryValidationFailure]


# クエリヘルプと補完サービスの型
class QueryHelpInfo(TypedDict):
    """クエリヘルプ情報"""
    description: str
    syntax: Optional[str]
    example: Optional[str]
    shacl_constraints: Optional[str]
    tips: Optional[str]
    commands: Optional[str]
    design_specific: Optional[str]
    examples: Optional[str]


class QueryHelpResult(TypedDict):
    """クエリヘルプ結果"""
    success: bool
    help: QueryHelpInfo


class SuggestionItem(TypedDict):
    """クエリ補完候補アイテム"""
    type: str  # keyword, pattern, node_label, property, relationship, etc.
    value: str
    description: str


class SuggestionContext(TypedDict):
    """クエリ補完コンテキスト"""
    stage: str  # start, node_selection, query_continuation, completed, etc.
    message: str
    query_type: Optional[str]  # match, create, set, etc.
    node_types: Optional[List[str]]  # 検出されたノードタイプ
    relationship_types: Optional[List[str]]  # 検出された関係タイプ
    properties: Optional[List[str]]  # 検出されたプロパティ


class SuggestionResult(TypedDict):
    """クエリ補完候補結果"""
    success: bool
    suggestions: List[SuggestionItem]
    context: SuggestionContext
    constraints: Optional[SHACLConstraintInfo]  # 関連するSHACL制約情報


class CompletionContext(TypedDict):
    """クエリ補完コンテキスト（詳細）"""
    stage: str  # 補完ステージ
    message: str
    current_token: Optional[str]  # 現在入力中のトークン
    current_position: Optional[int]  # 現在のカーソル位置


class CompletionResult(TypedDict):
    """クエリ補完結果（詳細）"""
    success: bool
    completions: List[SuggestionItem]
    context: CompletionContext
    analysis: Dict[str, Any]


class QuerySuggestionResult(TypedDict):
    """対話的クエリ補完結果"""
    success: bool
    message: str
    suggestions: List[SuggestionItem]
    constraints: Optional[SHACLConstraintInfo]  # 関連するSHACL制約情報
    analysis: Optional[Dict[str, Any]]  # クエリ解析結果


# フォールバックサジェスト用の型
class FallbackSuggestion(TypedDict):
    """フォールバックサジェスト項目"""
    type: str  # fallback, hint, example, etc.
    value: str
    description: str
    priority: Optional[int]  # 表示優先度


class PatternExampleInfo(TypedDict):
    """パターン例文情報"""
    pattern: str  # パターン文字列
    description: str  # 説明
    node_types: List[str]  # 含まれるノードタイプ
    properties: List[str]  # 含まれるプロパティ
    constraints: List[str]  # 関連する制約


# SHACLエラーフィードバックの拡張型
class EnhancedSHACLViolationDisplay(TypedDict):
    """拡張SHACL制約違反表示用データ"""
    message: str  # 表示メッセージ
    property: Optional[str]  # プロパティ名
    node_type: Optional[str]  # ノードタイプ
    value: Optional[str]  # 違反値
    suggestion: str  # 修正提案
    severity: Literal["error", "warning", "info"]  # 重要度
    example: Optional[str]  # 修正例
    query_pattern: Optional[str]  # 関連するクエリパターン


class EnhancedSHACLFeedback(TypedDict):
    """拡張SHACL検証フィードバック"""
    is_valid: bool  # 検証結果
    message: str  # 全体メッセージ
    violations: List[EnhancedSHACLViolationDisplay]  # 違反リスト
    suggestions: List[str]  # 修正提案リスト
    constraint_info: Optional[SHACLConstraintInfo]  # 関連する制約情報
    examples: List[PatternExampleInfo]  # 修正例文リスト


# 拡張されたクエリ補完コンテキスト
class EnhancedSuggestionContext(TypedDict):
    """拡張されたクエリ補完コンテキスト"""
    stage: str  # 補完ステージ
    message: str  # メッセージ
    pattern: Optional[str]  # 検出されたパターン
    constraints: Optional[SHACLConstraintInfo]  # 関連する制約情報


# 拡張されたクエリ補完結果
class EnhancedSuggestionResult(TypedDict):
    """拡張されたクエリ補完結果"""
    success: bool
    message: str
    suggestions: List[SuggestionItem]
    context: Optional[EnhancedSuggestionContext]
    constraints: Optional[SHACLConstraintInfo]
    analysis: Optional[Dict[str, Any]]


# 初期化サービスの処理結果型
class ProcessSuccess(TypedDict):
    """処理成功結果"""
    success: Literal[True]
    message: str
    file: Optional[str]
    nodes_count: Optional[int]
    edges_count: Optional[int]
    processed_files: Optional[List[str]]
    total_nodes: Optional[int]
    total_edges: Optional[int]
    root_nodes: Optional[List[Dict[str, Any]]]


class ProcessError(TypedDict):
    """処理エラー"""
    success: Literal[False]
    message: str
    error_type: Optional[str]
    details: Optional[Dict[str, Any]]


ProcessResult = Union[ProcessSuccess, ProcessError]

# 初期化サービスの追加型定義
class NodeParseSuccess(TypedDict):
    """ノード解析成功結果"""
    nodes: List[Any]  # InitNodeリスト
    edges: List[Any]  # InitEdgeリスト

class NodeParseError(TypedDict):
    """ノード解析エラー"""
    code: str
    message: str
    details: Optional[Dict[str, Any]]

NodeParseResult = Union[NodeParseSuccess, NodeParseError]

class ValidationSuccess(TypedDict):
    """検証成功結果"""
    is_valid: Literal[True]
    message: str

class ValidationError(TypedDict):
    """検証エラー"""
    is_valid: Literal[False]
    message: str
    duplicate_ids: List[str]

ValidationResult = Union[ValidationSuccess, ValidationError]

class NodeInsertionSuccess(TypedDict):
    """ノード挿入成功結果"""
    success: Literal[True]
    nodes_inserted: int
    nodes_skipped: int

class NodeInsertionError(TypedDict):
    """ノード挿入エラー"""
    success: Literal[False]
    message: str
    error_type: str
    nodes_inserted: int
    nodes_skipped: int

NodeInsertionResult = Union[NodeInsertionSuccess, NodeInsertionError]

class EdgeInsertionSuccess(TypedDict):
    """エッジ挿入成功結果"""
    success: Literal[True]
    edges_inserted: int
    edges_skipped: int

class EdgeInsertionError(TypedDict):
    """エッジ挿入エラー"""
    success: Literal[False]
    message: str
    error_type: str
    edges_inserted: int
    edges_skipped: int

EdgeInsertionResult = Union[EdgeInsertionSuccess, EdgeInsertionError]


# ヘルパー関数
def is_error(result: Any) -> bool:
    """結果がエラーかどうかを判定する
    
    Args:
        result: 判定対象の結果

    Returns:
        bool: エラーならTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "code" in result and "message" in result


def is_validation_failure(result: SHACLValidationResult) -> bool:
    """検証結果が失敗かどうかを判定する
    
    Args:
        result: 判定対象の検証結果

    Returns:
        bool: 検証失敗ならTrue、それ以外はFalse
    """
    return isinstance(result, dict) and "is_valid" in result and result["is_valid"] is False


# テスト関数
def test_is_error() -> None:
    """is_error関数のテスト"""
    # エラーの場合
    error_result: FunctionTypeCreationError = {"code": "TEST_ERROR", "message": "テストエラー"}
    assert is_error(error_result) is True
    
    # 正常データの場合
    success_result: FunctionTypeCreationSuccess = {
        "title": "TestFunction",
        "description": "Test description",
        "message": "関数型が正常に作成されました"
    }
    assert is_error(success_result) is False


def test_is_validation_failure() -> None:
    """is_validation_failure関数のテスト"""
    # 検証成功の場合
    success_result: SHACLValidationSuccess = {
        "is_valid": True,
        "report": "検証に成功しました"
    }
    assert is_validation_failure(success_result) is False
    
    # 検証失敗の場合
    failure_result: SHACLValidationFailure = {
        "is_valid": False,
        "report": "検証に失敗しました"
    }
    assert is_validation_failure(failure_result) is True
    
    # エラーの場合
    error_result: SHACLValidationError = {
        "code": "VALIDATION_ERROR",
        "message": "検証中にエラーが発生しました"
    }
    assert is_validation_failure(error_result) is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
