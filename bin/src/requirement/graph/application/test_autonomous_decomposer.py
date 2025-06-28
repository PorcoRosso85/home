"""
Tests for Autonomous Decomposer
"""
import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

import tempfile
import pytest
import kuzu
from datetime import datetime
from ..domain.types import Decision
from .autonomous_decomposer import create_autonomous_decomposer
from ..infrastructure.kuzu_repository import create_kuzu_repository
from ..infrastructure.llm_hooks_api import create_llm_hooks_api


@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def connection(db_path):
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # スキーマのセットアップ
    conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            status STRING,
            priority STRING,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            tags STRING[],
            embedding DOUBLE[],
            decomposition_aspect STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS PARENT_OF (
            FROM RequirementEntity TO RequirementEntity
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS DEPENDS_ON (
            FROM RequirementEntity TO RequirementEntity,
            type STRING DEFAULT 'depends_on',
            reason STRING DEFAULT ''
        )
    """)
    
    return conn


def test_decompose_requirement_hierarchical_creates_children(connection):
    """decompose_requirement_階層的分解_子要件を作成"""
    repository = create_kuzu_repository(connection)
    
    # 初期要件を作成
    parent_req = {
        "id": "req_001",
        "title": "Vision for RGL System",
        "description": "Requirement Graph Logic system",
        "status": "proposed",
        "priority": "high",
        "created_at": datetime.now(),
        "embedding": [0.1] * 50
    }
    repository["save"](parent_req)
    
    # モックLLM Hooks API
    class MockLLMHooksAPI:
        def __init__(self, conn):
            self.conn = conn
            
        def query(self, request):
            if request.get("query_type") == "score_requirements":
                return {"status": "success", "scores": [0.5] * len(request.get("requirement_ids", []))}
            if request.get("query") == "find_children":
                return {"status": "success", "data": []}
            return {"status": "success", "result": "ok"}
    
    mock_hooks = MockLLMHooksAPI(connection)
    
    # サービス作成
    decomposer = create_autonomous_decomposer(repository, mock_hooks)
    
    # 階層的分解を実行
    result = decomposer["decompose_requirement"]("req_001", "hierarchical", max_depth=3, target_size=5)
    
    assert result["status"] == "success"
    assert result["decomposed_count"] == 5
    assert len(saved_requirements) == 5
    
    # 親から子への分解を確認
    for req, parent_id in saved_requirements:
        assert parent_id == "req_001"
        assert any(aspect in req.get("decomposition_aspect", "") for aspect in ["architecture", "implementation", "testing", "deployment", "monitoring"])


def test_analyze_decomposition_quality_calculates_metrics(connection):
    """analyze_decomposition_quality_品質分析_メトリクスを計算"""
    repository = create_kuzu_repository(connection)
    
    # 親要件を作成
    parent = {
        "id": "req_001",
        "title": "Parent Requirement",
        "description": "Parent",
        "status": "approved",
        "priority": "high",
        "created_at": datetime.now(),
        "embedding": [0.1] * 50
    }
    repository["save"](parent)
    
    # 子要件を作成
    for i in range(1, 6):
        child = {
            "id": f"req_001_0{i}",
            "title": f"Child {i}",
            "description": f"Child requirement {i}",
            "status": "proposed",
            "priority": "medium",
            "created_at": datetime.now(),
            "embedding": [0.1] * 50
        }
        repository["save"](child, parent_id="req_001")
    
    # モックLLM Hooks API
    mock_hooks = create_mock_llm_hooks_with_connection(connection)
    mock_hooks["set_children"]("req_001", [
        {"id": "req_001_01", "title": "Child 1"},
        {"id": "req_001_02", "title": "Child 2"},
        {"id": "req_001_03", "title": "Child 3"},
        {"id": "req_001_04", "title": "Child 4"},
        {"id": "req_001_05", "title": "Child 5"}
    ])
    
    decomposer = create_autonomous_decomposer(repository, mock_hooks)
    
    # 品質分析
    quality = decomposer["analyze_decomposition_quality"]("req_001")
    
    assert "completeness" in quality
    assert "balance" in quality
    assert "coverage" in quality
    assert "issues" in quality
    assert quality["completeness"] == 1.0  # 5個の子要件は理想的


def test_suggest_refinements_detects_issues(connection):
    """suggest_refinements_問題検出_改善提案を生成"""
    repository = create_kuzu_repository(connection)
    
    # 親要件を作成
    parent = {
        "id": "req_001",
        "title": "Parent Requirement",
        "description": "Parent",
        "status": "approved",
        "priority": "high",
        "created_at": datetime.now(),
        "embedding": [0.1] * 50
    }
    repository["save"](parent)
    
    # 子要件が1つだけ
    child = {
        "id": "req_001_01",
        "title": "Only child",
        "description": "Single child requirement",
        "status": "proposed",
        "priority": "medium",
        "created_at": datetime.now(),
        "embedding": [0.1] * 50
    }
    repository["save"](child, parent_id="req_001")
    
    # モックLLM Hooks API
    mock_hooks = create_mock_llm_hooks_with_connection(connection)
    mock_hooks["set_children"]("req_001", [
        {"id": "req_001_01", "title": "Only child"}
    ])
    
    decomposer = create_autonomous_decomposer(repository, mock_hooks)
    
    # 改善提案を取得
    refinements = decomposer["suggest_refinements"]("req_001")
    
    assert len(refinements) > 0
    assert any(r["type"] == "add_children" for r in refinements)


# テスト用モック関数
def create_mock_llm_hooks():
    """テスト用のモックLLM Hooks APIを作成"""
    children_data = {}
    
    def set_children(parent_id, children):
        children_data[parent_id] = children
    
    def query(request):
        query_type = request.get("type")
        
        if query_type == "template":
            if request["query"] == "find_children":
                parent_id = request["parameters"]["parent_id"]
                return {
                    "status": "success",
                    "data": children_data.get(parent_id, [])
                }
            elif request["query"] == "calculate_progress":
                req_id = request["parameters"]["req_id"]
                children = children_data.get(req_id, [])
                if children:
                    return {
                        "status": "success",
                        "data": [{
                            "total": len(children),
                            "completed": 0,
                            "progress": 0.0
                        }]
                    }
        elif query_type == "procedure":
            if request["procedure"] == "requirement.validate":
                return {
                    "status": "success",
                    "data": [(True, [])]  # 違反なし
                }
        
        return {"status": "error", "error": "Unknown query"}
    
    return {
        "query": query,
        "set_children": set_children,
        "_children_data": children_data  # デバッグ用
    }


def create_mock_llm_hooks_with_connection(connection):
    """コネクションを使用するモックLLM Hooks APIを作成"""
    children_data = {}
    
    def set_children(parent_id, children):
        children_data[parent_id] = children
    
    def query(request):
        query_type = request.get("type")
        
        if query_type == "template":
            if request["query"] == "find_children":
                parent_id = request["parameters"]["parent_id"]
                return {
                    "status": "success",
                    "data": children_data.get(parent_id, [])
                }
            elif request["query"] == "calculate_progress":
                req_id = request["parameters"]["req_id"]
                children = children_data.get(req_id, [])
                if children:
                    return {
                        "status": "success",
                        "data": [{
                            "total": len(children),
                            "completed": 0,
                            "progress": 0.0
                        }]
                    }
        elif query_type == "procedure":
            if request["procedure"] == "requirement.validate":
                return {
                    "status": "success",
                    "data": [(True, [])]  # 違反なし
                }
        
        return {"status": "error", "error": "Unknown query"}
    
    return {
        "query": query,
        "set_children": set_children,
        "_children_data": children_data  # デバッグ用
    }