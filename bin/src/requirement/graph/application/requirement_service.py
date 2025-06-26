"""
Requirement Service - 要件管理とグラフ探索
依存: domain層のみ
外部依存: なし
"""
from typing import List, Dict, Callable, Optional, Union
from ..domain.types import Decision, DecisionResult, DecisionError
from ..domain.decision import create_decision
from ..domain.embedder import create_embedding
from ..domain.constraints import (
    validate_no_circular_dependency,
    validate_max_depth,
    validate_implementation_completeness
)


# Repository型定義（依存性注入用）
RequirementRepository = Dict[str, Callable]


def create_requirement_service(repository: RequirementRepository):
    """
    RequirementServiceを作成（依存性注入）
    
    Args:
        repository: KuzuDBリポジトリ
        
    Returns:
        RequirementService関数の辞書
    """
    
    def create_requirement(
        title: str,
        description: str,
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None
    ) -> DecisionResult:
        """要件を作成し、階層構造に配置"""
        import time
        requirement_id = f"req_{int(time.time() * 1000) % 1000000}"
        
        # 埋め込み生成
        embedding_result = create_embedding(f"{title} {description}")
        if "type" in embedding_result:
            return embedding_result
        
        # 要件作成
        requirement_result = create_decision(
            id=requirement_id,
            title=title,
            description=description,
            tags=tags,
            embedding=embedding_result
        )
        
        if "type" in requirement_result:
            return requirement_result
        
        # 親子関係を設定する前に階層深さチェック
        if parent_id:
            # 親の存在確認
            parent = repository["find"](parent_id)
            if "type" in parent:
                return parent  # エラーをそのまま返す
            
            # 階層深さチェック - 祖先を辿って深さを計算
            ancestors = repository["find_ancestors"](parent_id, depth=10)
            current_depth = len(ancestors) + 1  # 親の深さ + 1
            
            if current_depth >= 5:  # 0ベースで5階層まで（L0-L4）
                return {
                    "type": "ConstraintViolationError",
                    "message": f"Maximum hierarchy depth (5) would be exceeded. Current depth: {current_depth}",
                    "constraint": "max_depth",
                    "details": [f"Parent has {len(ancestors)} ancestors"]
                }
        
        # 保存（parent_idも一緒に渡す）
        saved = repository["save"](requirement_result, parent_id)
        
        # 依存関係を設定
        if depends_on:
            for dep_id in depends_on:
                result = add_dependency(requirement_id, dep_id)
                if "type" in result:
                    return result
        
        return saved
    
    def add_dependency(
        from_id: str,
        to_id: str,
        dependency_type: str = "depends_on",
        reason: str = ""
    ) -> Dict:
        """要件間の依存関係を追加"""
        # 存在確認
        from_req = repository["find"](from_id)
        if "type" in from_req:
            return from_req
        
        to_req = repository["find"](to_id)
        if "type" in to_req:
            return to_req
        
        # 依存関係追加
        return repository["add_dependency"](from_id, to_id, dependency_type, reason)
    
    def find_dependencies(
        requirement_id: str,
        depth: int = 3,
        direction: str = "outgoing"
    ) -> List[Dict]:
        """依存関係を探索"""
        return repository["find_dependencies"](requirement_id, depth)
    
    def analyze_impact(
        requirement_id: str,
        depth: int = 3
    ) -> Dict:
        """要件変更の影響範囲を分析"""
        # 依存元を探索（この要件に依存している要件）
        # TODO: 逆方向の探索を実装
        dependencies = repository["find_dependencies"](requirement_id, depth)
        
        impact = {
            "requirement_id": requirement_id,
            "directly_affected": [],
            "indirectly_affected": [],
            "total_affected": len(dependencies)
        }
        
        for dep in dependencies:
            if dep["distance"] == 1:
                impact["directly_affected"].append(dep["requirement"])
            else:
                impact["indirectly_affected"].append(dep["requirement"])
        
        return impact
    
    def validate_constraints(requirement_id: str) -> List[Dict]:
        """制約違反をチェック"""
        violations = []
        
        # 依存関係の循環チェック
        deps = repository["find_dependencies"](requirement_id, 10)
        dep_ids = [d["requirement"]["id"] for d in deps]
        
        # 簡易的な全依存マップ（本来は全要件から構築）
        all_deps = {requirement_id: dep_ids}
        
        circular_check = validate_no_circular_dependency(
            requirement_id, dep_ids, all_deps
        )
        if isinstance(circular_check, dict):
            violations.append(circular_check)
        
        return violations
    
    def check_implementation_progress(requirement_id: str) -> Dict:
        """実装進捗を確認"""
        requirement = repository["find"](requirement_id)
        if "type" in requirement:
            return requirement
        
        # TODO: 実装情報とテスト情報を取得
        implementations = []  # 簡易実装
        tests = []  # 簡易実装
        
        return validate_implementation_completeness(
            requirement, implementations, tests
        )
    
    def find_implementation_path(
        from_requirement_id: str,
        to_code_path: str
    ) -> List[Dict]:
        """要件から実装へのパスを検索"""
        # TODO: LocationURIとの統合が必要
        # 簡易実装
        return [{
            "type": "path",
            "from": from_requirement_id,
            "to": to_code_path,
            "steps": ["Not implemented yet"]
        }]
    
    def find_ancestors(requirement_id: str, depth: int = 10) -> List[Dict]:
        """要件の祖先（親・祖父母など）を探索"""
        return repository["find_ancestors"](requirement_id, depth)
    
    def find_children(requirement_id: str, depth: int = 10) -> List[Dict]:
        """要件の子孫（子・孫など）を探索"""
        return repository["find_children"](requirement_id, depth)
    
    def find_abstract_requirement(requirement_id: str) -> Dict:
        """具体的な要件がどの抽象的な要件のためのものかを探索"""
        ancestors = repository["find_ancestors"](requirement_id, 10)
        
        # 最も抽象的な要件（L0タグを持つもの）を探す
        for ancestor in ancestors:
            req = ancestor["requirement"]
            if "L0_vision" in req.get("tags", []):
                return {
                    "abstract_requirement": req,
                    "path_length": ancestor["distance"],
                    "found": True
                }
        
        # L0が見つからなければ最も遠い祖先を返す
        if ancestors:
            return {
                "abstract_requirement": ancestors[-1]["requirement"],
                "path_length": ancestors[-1]["distance"],
                "found": True
            }
        
        return {
            "found": False,
            "message": f"No abstract requirement found for {requirement_id}"
        }
    
    return {
        "create_requirement": create_requirement,
        "add_dependency": add_dependency,
        "find_dependencies": find_dependencies,
        "analyze_impact": analyze_impact,
        "validate_constraints": validate_constraints,
        "check_implementation_progress": check_implementation_progress,
        "find_implementation_path": find_implementation_path,
        "find_ancestors": find_ancestors,
        "find_children": find_children,
        "find_abstract_requirement": find_abstract_requirement
    }


# Test cases
def test_requirement_service_create_with_dependencies_returns_saved():
    """requirement_service_create_依存関係付き作成_保存結果を返す"""
    # モックリポジトリ
    storage = {}
    dependencies = {}
    
    def mock_save(requirement, parent_id=None):
        storage[requirement["id"]] = requirement
        return requirement
    
    def mock_find(req_id):
        if req_id in storage:
            return storage[req_id]
        return {"type": "DecisionNotFoundError", "message": "Not found", "decision_id": req_id}
    
    def mock_add_dependency(from_id, to_id, dep_type, reason):
        if from_id not in dependencies:
            dependencies[from_id] = []
        dependencies[from_id].append({"to": to_id, "type": dep_type, "reason": reason})
        return {"success": True, "from": from_id, "to": to_id}
    
    def mock_find_dependencies(req_id, depth):
        return []
    
    repository = {
        "save": mock_save,
        "find": mock_find,
        "find_all": lambda: list(storage.values()),
        "add_dependency": mock_add_dependency,
        "find_dependencies": mock_find_dependencies,
        "find_ancestors": lambda req_id, depth: [],
        "find_children": lambda req_id, depth: []
    }
    
    service = create_requirement_service(repository)
    
    # 依存先を先に作成
    db_req = service["create_requirement"](
        title="データベース設計",
        description="PostgreSQL設定",
        tags=["infrastructure"]
    )
    
    # 依存関係付きで作成
    auth_req = service["create_requirement"](
        title="認証システム",
        description="OAuth2.0実装",
        tags=["security"],
        depends_on=[db_req["id"]]
    )
    
    assert "type" not in auth_req
    assert auth_req["title"] == "認証システム"
    assert db_req["id"] in [d["to"] for d in dependencies.get(auth_req["id"], [])]


def test_requirement_service_analyze_impact_returns_affected_list():
    """requirement_service_影響分析_影響リストを返す"""
    storage = {
        "req_001": {"id": "req_001", "title": "Core"},
        "req_002": {"id": "req_002", "title": "Feature A"},
        "req_003": {"id": "req_003", "title": "Feature B"}
    }
    
    def mock_find_dependencies(req_id, depth):
        if req_id == "req_001":
            return [
                {"requirement": storage["req_002"], "distance": 1},
                {"requirement": storage["req_003"], "distance": 2}
            ]
        return []
    
    repository = {
        "save": lambda r, p=None: r,
        "find": lambda id: storage.get(id, {"type": "DecisionNotFoundError"}),
        "find_all": lambda: list(storage.values()),
        "add_dependency": lambda f, t, dt, r: {"success": True},
        "find_dependencies": mock_find_dependencies,
        "find_ancestors": lambda req_id, depth: [],
        "find_children": lambda req_id, depth: []
    }
    
    service = create_requirement_service(repository)
    
    impact = service["analyze_impact"]("req_001")
    
    assert impact["requirement_id"] == "req_001"
    assert len(impact["directly_affected"]) == 1
    assert len(impact["indirectly_affected"]) == 1
    assert impact["total_affected"] == 2


def test_create_requirement_hierarchy_creates_parent_of_relation():
    """要件階層作成_parent_id指定時_PARENT_OF関係が作成される"""
    import tempfile
    from ..infrastructure.kuzu_repository import create_kuzu_repository
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = create_kuzu_repository(f"{tmpdir}/test.db")
        service = create_requirement_service(repo)
        
        parent = service["create_requirement"](
            title="ビジョン",
            description="システムの目的",
            tags=["L0_vision"]
        )
        
        child = service["create_requirement"](
            title="アーキテクチャ",
            description="設計方針",
            parent_id=parent["id"],
            tags=["L1_architecture"]
        )
        
        ancestors = service["find_ancestors"](child["id"])
        assert len(ancestors) == 1
        assert ancestors[0]["requirement"]["id"] == parent["id"]
        assert ancestors[0]["distance"] == 1


def test_find_abstract_requirement_from_implementation_returns_vision():
    """抽象要件探索_L2実装から_L0ビジョンを返す"""
    import tempfile
    from ..infrastructure.kuzu_repository import create_kuzu_repository
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = create_kuzu_repository(f"{tmpdir}/test.db")
        service = create_requirement_service(repo)
        
        vision = service["create_requirement"](
            title="システムビジョン",
            description="最上位の目的",
            tags=["L0_vision"]
        )
        
        arch = service["create_requirement"](
            title="アーキテクチャ",
            description="中間層",
            parent_id=vision["id"],
            tags=["L1_architecture"]
        )
        
        impl = service["create_requirement"](
            title="具体実装",
            description="実装詳細",
            parent_id=arch["id"],
            tags=["L2_implementation"]
        )
        
        result = service["find_abstract_requirement"](impl["id"])
        
        assert result["found"] == True
        assert result["abstract_requirement"]["id"] == vision["id"]
        assert result["abstract_requirement"]["tags"] == ["L0_vision"]
        assert result["path_length"] == 2


def test_hierarchy_depth_limit_prevents_deep_nesting():
    """階層深さ制限_6階層目作成時_エラーを返す"""
    import tempfile
    from ..infrastructure.kuzu_repository import create_kuzu_repository
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = create_kuzu_repository(f"{tmpdir}/test.db")
        service = create_requirement_service(repo)
        
        # 5階層まで作成
        l0 = service["create_requirement"](
            title="L0", description="Level 0", tags=["L0"]
        )
        
        l1 = service["create_requirement"](
            title="L1", description="Level 1", parent_id=l0["id"], tags=["L1"]
        )
        
        l2 = service["create_requirement"](
            title="L2", description="Level 2", parent_id=l1["id"], tags=["L2"]
        )
        
        l3 = service["create_requirement"](
            title="L3", description="Level 3", parent_id=l2["id"], tags=["L3"]
        )
        
        l4 = service["create_requirement"](
            title="L4", description="Level 4", parent_id=l3["id"], tags=["L4"]
        )
        
        # 6階層目はエラー
        l5_result = service["create_requirement"](
            title="L5", description="Level 5", parent_id=l4["id"], tags=["L5"]
        )
        
        assert l5_result["type"] == "ConstraintViolationError"
        assert l5_result["constraint"] == "max_depth"
        assert "exceed" in l5_result["message"].lower()
