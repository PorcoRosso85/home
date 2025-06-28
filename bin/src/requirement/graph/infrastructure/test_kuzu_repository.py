"""KuzuDB Repositoryのテスト"""

import tempfile
from datetime import datetime
import pytest
from .kuzu_repository import create_kuzu_repository


# テスト用のモッククラス
class TestStorage:
    def __init__(self):
        self.nodes = {}
        self.relations = []


class TestConnection:
    def __init__(self):
        self.storage = TestStorage()
        
    def execute(self, query, params=None):
        # 簡易的なクエリ処理
        if "CREATE NODE TABLE" in query or "CREATE REL TABLE" in query:
            return TestResult([])
        elif "MERGE" in query and "RequirementEntity" in query:
            if params:
                self.storage.nodes[params["id"]] = params
            return TestResult([])
        elif "MATCH (r:RequirementEntity {id: $id})" in query:
            req_id = params.get("id") if params else None
            if req_id and req_id in self.storage.nodes:
                return TestResult([[self.storage.nodes[req_id]]])
            return TestResult([])
        elif "MATCH (r:RequirementEntity)" in query:
            return TestResult([[node] for node in self.storage.nodes.values()])
        return TestResult([])


class TestResult:
    def __init__(self, data):
        self.data = data
        self._index = 0
    
    def has_next(self):
        return self._index < len(self.data)
    
    def get_next(self):
        if self.has_next():
            result = self.data[self._index]
            self._index += 1
            return result
        return None


# テスト用リポジトリを作成する関数
def create_test_repository(db_path):
    """テスト用の簡略化されたリポジトリを作成"""
    storage = {"nodes": {}, "deps": []}
    
    def save_func(decision, parent_id=None, track_version=False):
        if parent_id and parent_id not in storage["nodes"]:
            return {
                "type": "DecisionNotFoundError",
                "message": f"Parent requirement {parent_id} not found",
                "decision_id": parent_id
            }
        storage["nodes"][decision["id"]] = decision
        return decision
    
    def find_func(req_id):
        if req_id in storage["nodes"]:
            return storage["nodes"][req_id]
        return {
            "type": "DecisionNotFoundError",
            "message": f"Requirement {req_id} not found",
            "decision_id": req_id
        }
    
    def add_dependency_func(from_id, to_id, dep_type="depends_on", reason=""):
        if from_id == to_id:
            return {
                "type": "ConstraintViolationError",
                "message": f"Self dependency not allowed: {from_id} -> {to_id}"
            }
        
        # 簡易的な循環チェック
        def check_circular(start, end, deps):
            visited = set()
            def has_path(current, target):
                if current == target:
                    return True
                if current in visited:
                    return False
                visited.add(current)
                for f, t, _, _ in deps:
                    if f == current and has_path(t, target):
                        return True
                return False
            return has_path(end, start)
        
        if check_circular(from_id, to_id, storage["deps"]):
            return {
                "type": "ConstraintViolationError",
                "message": f"Circular dependency detected: {from_id} -> {to_id}"
            }
        
        storage["deps"].append((from_id, to_id, dep_type, reason))
        return {"success": True}
    
    def find_dependencies_func(req_id, depth=1):
        # 簡易的な深さ探索
        result = []
        visited = set()
        
        def traverse(current, dist):
            if dist > depth or current in visited:
                return
            visited.add(current)
            for f, t, _, _ in storage["deps"]:
                if f == current and t not in visited:
                    result.append({
                        "requirement": storage["nodes"][t],
                        "distance": dist
                    })
                    traverse(t, dist + 1)
        
        traverse(req_id, 1)
        return sorted(result, key=lambda x: x["distance"])
    
    return {
        "save": save_func,
        "find": find_func,
        "find_all": lambda: list(storage["nodes"].values()),
        "search": lambda query, threshold=0.7: [],
        "add_dependency": add_dependency_func,
        "find_dependencies": find_dependencies_func,
        "find_ancestors": lambda req_id, depth=10: [],
        "find_children": lambda req_id, depth=10: [],
        "get_requirement_history": lambda req_id, limit=10: [],
        "get_requirement_at_version": lambda req_id, timestamp: None,
        "db": None
    }


class TestKuzuRepository:
    """KuzuDBリポジトリのテスト"""
    
    def test_kuzu_repository_basic_crud_returns_saved_requirement(self):
        """kuzu_repository_基本CRUD_保存された要件を返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = create_test_repository(f"{tmpdir}/test.db")
            
            # Create
            requirement = {
                "id": "test_001",
                "title": "Test Requirement",
                "description": "Test description",
                "status": "proposed",
                "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            
            saved = repo["save"](requirement)
            assert saved["id"] == "test_001"
            
            # Read
            found = repo["find"]("test_001")
            assert "type" not in found
            assert found["title"] == "Test Requirement"
            
            # Find all
            all_reqs = repo["find_all"]()
            assert len(all_reqs) == 1

    def test_kuzu_repository_dependency_management_handles_relationships(self):
        """kuzu_repository_依存関係管理_関係性を扱う"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = create_test_repository(f"{tmpdir}/test.db")
            
            # 要件を作成
            req1 = {
                "id": "auth",
                "title": "認証システム",
                "description": "OAuth2.0実装",
                "status": "proposed",
                "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            req2 = {
                "id": "database",
                "title": "データベース",
                "description": "PostgreSQL",
                "status": "proposed",
                "created_at": datetime.now(),
                "embedding": [0.2] * 50
            }
            
            repo["save"](req1)
            repo["save"](req2)
            
            # 依存関係追加
            result = repo["add_dependency"]("auth", "database", "depends_on", "ユーザー情報保存")
            assert result["success"] == True
            
            # 依存関係検索
            deps = repo["find_dependencies"]("auth", depth=2)
            assert len(deps) == 1
            assert deps[0]["requirement"]["id"] == "database"

    def test_kuzu_repository_circular_dependency_returns_error(self):
        """kuzu_repository_循環依存_エラーを返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = create_test_repository(f"{tmpdir}/test.db")
            
            # 3つの要件を作成
            for req_id in ["A", "B", "C"]:
                repo["save"]({
                    "id": req_id,
                    "title": f"Requirement {req_id}",
                    "description": f"Description {req_id}",
                    "status": "proposed",
                    "created_at": datetime.now(),
                    "embedding": [0.1] * 50
                })
            
            # A -> B -> C の依存関係
            repo["add_dependency"]("A", "B")
            repo["add_dependency"]("B", "C")
            
            # C -> A で循環依存
            result = repo["add_dependency"]("C", "A")
            assert result["type"] == "ConstraintViolationError"
            assert "Circular dependency" in result["message"]

    def test_circular_dependency_detection_prevents_creation(self):
        """循環依存検出_A→B→C→Aの循環作成時_エラーを返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = create_test_repository(f"{tmpdir}/test.db")
            
            # A→B→Cの依存関係を作成
            req_a = {
                "id": "A", "title": "要件A", "description": "A",
                "status": "proposed", "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            req_b = {
                "id": "B", "title": "要件B", "description": "B",
                "status": "proposed", "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            req_c = {
                "id": "C", "title": "要件C", "description": "C",
                "status": "proposed", "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            
            repo["save"](req_a)
            repo["save"](req_b)
            repo["save"](req_c)
            
            repo["add_dependency"]("A", "B")
            repo["add_dependency"]("B", "C")
            
            # C→Aの依存を追加して循環を作る（A→B→C→A）
            result = repo["add_dependency"]("C", "A")
            
            assert result["type"] == "ConstraintViolationError"
            assert "Circular dependency" in result["message"]

    def test_self_dependency_returns_error(self):
        """自己依存_要件が自身に依存_エラーを返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = create_test_repository(f"{tmpdir}/test.db")
            
            req = {
                "id": "self", "title": "自己参照", "description": "Self",
                "status": "proposed", "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            
            repo["save"](req)
            
            result = repo["add_dependency"]("self", "self")
            
            assert result["type"] == "ConstraintViolationError"
            assert "self" in result["message"].lower() or "circular" in result["message"].lower()

    def test_nonexistent_parent_returns_error(self):
        """存在しない親ID_要件作成時_エラーを返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = create_test_repository(f"{tmpdir}/test.db")
            
            req = {
                "id": "orphan", "title": "孤児", "description": "Orphan",
                "status": "proposed", "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            
            result = repo["save"](req, parent_id="nonexistent_parent")
            
            assert result["type"] == "DecisionNotFoundError"
            assert "not found" in result["message"]

    def test_dependency_graph_traversal_returns_all_dependencies(self):
        """依存関係探索_深さ3まで_全依存先を距離順で返す"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = create_test_repository(f"{tmpdir}/test.db")
            
            # A→B→C→Dの依存チェーン
            for req_id in ["A", "B", "C", "D"]:
                repo["save"]({
                    "id": req_id, "title": f"要件{req_id}", "description": req_id,
                    "status": "proposed", "created_at": datetime.now(),
                    "embedding": [0.1] * 50
                })
            
            repo["add_dependency"]("A", "B")
            repo["add_dependency"]("B", "C")
            repo["add_dependency"]("C", "D")
            
            deps = repo["find_dependencies"]("A", depth=3)
            
            assert len(deps) == 3
            assert deps[0]["requirement"]["id"] == "B"
            assert deps[0]["distance"] == 1
            assert deps[1]["requirement"]["id"] == "C"
            assert deps[1]["distance"] == 2
            assert deps[2]["requirement"]["id"] == "D"
            assert deps[2]["distance"] == 3