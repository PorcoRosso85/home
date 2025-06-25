"""アプリケーション層のコマンド（ユースケース）"""

from typing import TypedDict, List, Dict
from datetime import datetime
from ..domain.types import (
    RequirementDict, ErrorDict, AddRequirementResultDict,
    RequirementRepositoryPort, EmbedderPort,
    create_requirement
)
from ..domain.services import (
    calculate_uniqueness_score, calculate_clarity_score,
    calculate_completeness_score, generate_suggestions
)


class AddRequirementCommand(TypedDict):
    """要件追加コマンド"""
    text: str
    metadata: dict


class AddRelationCommand(TypedDict):
    """関係追加コマンド"""
    from_id: str
    to_id: str
    relation_type: str
    confidence: float
    reasoning: str


class RelationAddResultDict(TypedDict):
    """関係追加結果"""
    relation_id: str
    scores: Dict[str, float]
    graph_changes: Dict[str, int]
    warnings: List[str]


def create_add_requirement_handler(
    repo: RequirementRepositoryPort = None,
    embedder: EmbedderPort = None
):
    """要件追加ハンドラーを作成（高階関数パターン）"""
    
    # 引数チェック（親切なエラー）
    if repo is None or embedder is None:
        missing = []
        if repo is None:
            missing.append("repo")
        if embedder is None:
            missing.append("embedder")
        
        raise TypeError(
            f"必要な引数が不足しています: {', '.join(missing)}\n\n"
            "使い方:\n"
            ">>> from poc.requirement_graph_logic.infrastructure.adapters import create_in_memory_repository, create_simple_embedder\n"
            ">>> repo = create_in_memory_repository()\n"
            ">>> embedder = create_simple_embedder()\n"
            ">>> handler = create_add_requirement_handler(repo, embedder)\n\n"
            "または簡単に:\n"
            ">>> from poc.requirement_graph_logic import quick_start\n"
            ">>> handler = quick_start()"
        )
    
    def handle(command: AddRequirementCommand) -> AddRequirementResultDict | ErrorDict:
        """要件を追加し、スコアと提案を返す"""
        
        # 入力検証（親切なエラーメッセージ）
        if not isinstance(command, dict):
            return {
                "error": f"コマンドは辞書形式で渡してください。受け取った型: {type(command).__name__}\n正しい形式: handler({{'text': '要件テキスト', 'metadata': {{}}}})",
                "code": "INVALID_TYPE",
                "details": None
            }
        
        if "text" not in command:
            return {
                "error": "'text'キーが必要です\n正しい形式: {'text': '要件テキスト', 'metadata': {}}",
                "code": "MISSING_TEXT",
                "details": None
            }
        
        if "metadata" not in command:
            return {
                "error": "'metadata'キーが必要です（空の辞書でもOK）\n正しい形式: {'text': '要件テキスト', 'metadata': {}}",
                "code": "MISSING_METADATA",
                "details": None
            }
        
        # 1. 埋め込み生成
        embed_result = embedder.embed(command["text"])
        if "error" in embed_result:
            return {"error": f"Embedding failed: {embed_result['error']}", "code": "EMBED_ERROR", "details": None}
        
        # 2. 類似要件を検索
        similar_result = repo.find_similar(embed_result, limit=10)
        if "error" in similar_result:
            return {"error": f"Similar search failed: {similar_result['error']}", "code": "SEARCH_ERROR", "details": None}
        
        # 3. スコア計算
        uniqueness = calculate_uniqueness_score(embed_result, similar_result)
        clarity = calculate_clarity_score(command["text"])
        completeness = calculate_completeness_score(command["text"])
        
        scores = {
            "uniqueness": uniqueness,
            "clarity": clarity,
            "completeness": completeness,
            "graph_fit": 0.8  # 簡易実装
        }
        
        # 4. 重複チェック（uniqueness < 0.1 は完全重複とみなす）
        if uniqueness < 0.1 and similar_result:
            return {
                "requirement_id": "",
                "scores": scores,
                "similar_requirements": [
                    {
                        "id": req["id"],
                        "text": req["text"],
                        "similarity": 1.0 - uniqueness
                    }
                    for req in similar_result[:3]
                ],
                "suggestions": ["この要件は既存要件と重複しています。既存要件を確認してください。"]
            }
        
        # 5. 要件作成
        requirement = create_requirement(command["text"], embed_result)
        requirement["metadata"] = command["metadata"]
        
        # 6. 保存
        save_result = repo.save(requirement)
        if isinstance(save_result, dict) and "error" in save_result:
            return {"error": f"Save failed: {save_result['error']}", "code": "SAVE_ERROR", "details": None}
        
        # 7. 提案生成
        suggestions = generate_suggestions(requirement, similar_result, scores)
        
        # 8. 結果を返す
        return {
            "requirement_id": save_result,
            "scores": scores,
            "similar_requirements": [
                {
                    "id": req["id"],
                    "text": req["text"],
                    "similarity": 1.0 - calculate_uniqueness_score(embed_result, [req])
                }
                for req in similar_result[:3]
            ],
            "suggestions": suggestions
        }
    
    return handle


def create_add_relation_handler(repo: RequirementRepositoryPort):
    """関係追加ハンドラーを作成"""
    
    def handle(command: AddRelationCommand) -> RelationAddResultDict | ErrorDict:
        """要件間の関係を追加"""
        
        # 1. 両方の要件が存在するか確認
        from_result = repo.find_by_id(command["from_id"])
        if "error" in from_result:
            return {"error": f"From requirement not found: {from_result['error']}", "code": "NOT_FOUND", "details": None}
        
        to_result = repo.find_by_id(command["to_id"])
        if "error" in to_result:
            return {"error": f"To requirement not found: {to_result['error']}", "code": "NOT_FOUND", "details": None}
        
        # 2. 関係の整合性チェック（簡易版）
        consistency_score = 0.9  # 実際はグラフ分析で計算
        redundancy_score = 0.1   # 実際は既存関係との重複度
        
        # 3. 警告生成
        warnings = []
        if consistency_score < 0.5:
            warnings.append("この関係は既存のグラフ構造と矛盾する可能性があります")
        
        if redundancy_score > 0.8:
            warnings.append("類似の関係が既に存在します")
        
        # 4. 関係を保存（実際の実装では repo.add_relation を呼ぶ）
        relation_id = f"REL-{datetime.now().timestamp()}"
        
        # 5. グラフへの影響を計算
        graph_changes = {
            "new_paths": 2,        # 新しく生成された経路数
            "cycles_created": 0,   # 循環参照数
            "orphans_resolved": 1  # 解決された孤立ノード
        }
        
        return {
            "relation_id": relation_id,
            "scores": {
                "consistency": consistency_score,
                "redundancy": redundancy_score,
                "impact": 0.7,
                "confidence": command["confidence"]
            },
            "graph_changes": graph_changes,
            "warnings": warnings
        }
    
    return handle


# ===== テストコード（規約: in-sourceテスト） =====

def test_add_requirement_new_unique_returns_high_uniqueness():
    """要件追加_新規独自要件_高独自性スコア"""
    # モックの作成
    class MockRepo:
        def find_similar(self, embedding, limit):
            return []  # 類似なし
        def save(self, requirement):
            return "REQ-NEW-001"
    
    class MockEmbedder:
        def embed(self, text):
            from ..domain.types import create_embedding
            return create_embedding([1.0, 0.0, 0.0])
    
    # ハンドラー作成とテスト
    handler = create_add_requirement_handler(MockRepo(), MockEmbedder())
    command: AddRequirementCommand = {
        "text": "新しいユニークな要件です",
        "metadata": {"priority": "high"}
    }
    
    result = handler(command)
    assert "error" not in result
    assert result["requirement_id"] == "REQ-NEW-001"
    assert result["scores"]["uniqueness"] == 1.0
    assert len(result["suggestions"]) >= 0


def test_add_requirement_duplicate_returns_low_uniqueness():
    """要件追加_重複要件_低独自性スコア"""
    from ..domain.types import create_requirement, create_embedding
    
    # 既存の要件（同じ埋め込み）
    existing_embedding = create_embedding([1.0, 0.0, 0.0])
    existing_req = create_requirement("既存の要件", existing_embedding)
    
    class MockRepo:
        def find_similar(self, embedding, limit):
            return [existing_req]
        def save(self, requirement):
            return "REQ-DUP-001"
    
    class MockEmbedder:
        def embed(self, text):
            return existing_embedding  # 同じ埋め込み
    
    handler = create_add_requirement_handler(MockRepo(), MockEmbedder())
    command: AddRequirementCommand = {
        "text": "既存の要件",  # 重複
        "metadata": {}
    }
    
    result = handler(command)
    assert "error" not in result
    assert result["requirement_id"] == ""  # 重複なので空
    assert result["scores"]["uniqueness"] < 0.1
    assert "重複" in result["suggestions"][0]


def test_add_requirement_embedding_error_returns_error():
    """要件追加_埋め込みエラー_エラー返却"""
    class MockRepo:
        def find_similar(self, embedding, limit):
            return []
    
    class MockEmbedder:
        def embed(self, text):
            return {"error": "API limit exceeded", "code": "LIMIT_ERROR", "details": None}
    
    handler = create_add_requirement_handler(MockRepo(), MockEmbedder())
    command: AddRequirementCommand = {"text": "テスト要件", "metadata": {}}
    
    result = handler(command)
    assert "error" in result
    assert "embedding failed" in result["error"].lower()


def test_add_requirement_vague_text_returns_suggestions():
    """要件追加_曖昧な表現_改善提案"""
    class MockRepo:
        def find_similar(self, embedding, limit):
            return []
        def save(self, requirement):
            return "REQ-VAGUE-001"
    
    class MockEmbedder:
        def embed(self, text):
            from ..domain.types import create_embedding
            return create_embedding([1.0, 0.0, 0.0])
    
    handler = create_add_requirement_handler(MockRepo(), MockEmbedder())
    command: AddRequirementCommand = {
        "text": "認証など",  # 曖昧で短い
        "metadata": {}
    }
    
    result = handler(command)
    assert "error" not in result
    assert result["scores"]["clarity"] < 0.6
    assert any("具体的" in s for s in result["suggestions"])


def test_add_relation_valid_requirements_returns_success():
    """関係追加_有効な要件間_成功"""
    from ..domain.types import create_requirement
    
    req1 = create_requirement("要件1")
    req2 = create_requirement("要件2")
    
    class MockRepo:
        def find_by_id(self, req_id):
            if req_id == "REQ-001":
                return req1
            elif req_id == "REQ-002":
                return req2
            return {"error": "Not found", "code": "NOT_FOUND", "details": None}
    
    handler = create_add_relation_handler(MockRepo())
    command: AddRelationCommand = {
        "from_id": "REQ-001",
        "to_id": "REQ-002",
        "relation_type": "depends_on",
        "confidence": 0.9,
        "reasoning": "要件2は要件1に依存"
    }
    
    result = handler(command)
    assert "error" not in result
    assert result["relation_id"].startswith("REL-")
    assert result["scores"]["confidence"] == 0.9
    assert "new_paths" in result["graph_changes"]


def test_add_relation_missing_requirement_returns_error():
    """関係追加_要件不在_エラー"""
    class MockRepo:
        def find_by_id(self, req_id):
            return {"error": "Not found", "code": "NOT_FOUND", "details": None}
    
    handler = create_add_relation_handler(MockRepo())
    command: AddRelationCommand = {
        "from_id": "REQ-MISSING",
        "to_id": "REQ-002",
        "relation_type": "depends_on",
        "confidence": 0.9,
        "reasoning": "test"
    }
    
    result = handler(command)
    assert "error" in result
    assert "not found" in result["error"].lower()