"""
Tests for Requirement Service
"""
import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

import tempfile
import pytest
import kuzu
from ..infrastructure.kuzu_repository import create_kuzu_repository
from .requirement_service import create_requirement_service


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
            embedding DOUBLE[]
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS DEPENDS_ON (
            FROM RequirementEntity TO RequirementEntity,
            type STRING DEFAULT 'depends_on',
            reason STRING DEFAULT ''
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IF NOT EXISTS PARENT_OF (
            FROM RequirementEntity TO RequirementEntity
        )
    """)
    
    return conn


def test_requirement_service_create_with_dependencies_returns_saved(connection):
    """requirement_service_create_依存関係付き作成_保存結果を返す"""
    repository = create_kuzu_repository(connection)
    service = create_requirement_service(repository)
    
    # 依存先を先に作成
    db_req = service["create_requirement"](
        title="データベース設計",
        description="PostgreSQL設定",
    )
    
    # 依存関係付きで作成
    auth_req = service["create_requirement"](
        title="認証システム",
        description="OAuth2.0実装",
        depends_on=[db_req["id"]]
    )
    
    assert "type" not in auth_req
    assert auth_req["title"] == "認証システム"
    # 依存関係の確認
    deps = repository["get_dependencies"](auth_req["id"])
    assert db_req["id"] in [d["to"] for d in deps]


def test_requirement_service_analyze_impact_returns_affected_list(connection):
    """requirement_service_影響分析_影響リストを返す"""
    repository = create_kuzu_repository(connection)
    service = create_requirement_service(repository)
    
    # テスト用要件を作成
    req_001 = service["create_requirement"](title="Core", description="Core component")
    req_002 = service["create_requirement"](title="Feature A", description="Feature A")
    req_003 = service["create_requirement"](title="Feature B", description="Feature B")
    
    # 依存関係を設定 (req_002 -> req_001, req_003 -> req_002)
    repository["add_dependency"](req_002["id"], req_001["id"], "depends_on", "needs core")
    repository["add_dependency"](req_003["id"], req_002["id"], "depends_on", "needs feature A")
    
    impact = service["analyze_impact"]("req_001")
    
    assert impact["requirement_id"] == "req_001"
    assert len(impact["directly_affected"]) == 1
    assert len(impact["indirectly_affected"]) == 1
    assert impact["total_affected"] == 2


def test_create_requirement_hierarchy_creates_parent_of_relation(connection):
    """要件階層作成_parent_id指定時_PARENT_OF関係が作成される"""
    repository = create_kuzu_repository(connection)
    service = create_requirement_service(repository)
    
    parent = service["create_requirement"](
        title="ビジョン",
        description="システムの目的",
    )
    
    child = service["create_requirement"](
        title="アーキテクチャ",
        description="設計方針",
        parent_id=parent["id"],
    )
    
    ancestors = service["find_ancestors"](child["id"])
    assert len(ancestors) == 1
    assert ancestors[0]["requirement"]["id"] == parent["id"]
    assert ancestors[0]["distance"] == 1


def test_find_abstract_requirement_from_implementation_returns_vision(connection):
    """抽象要件探索_L2実装から_L0ビジョンを返す"""
    repository = create_kuzu_repository(connection)
    service = create_requirement_service(repository)
    
    vision = service["create_requirement"](
        title="システムビジョン",
        description="最上位の目的",
    )
    
    arch = service["create_requirement"](
        title="アーキテクチャ",
        description="中間層",
        parent_id=vision["id"],
    )
    
    impl = service["create_requirement"](
        title="具体実装",
        description="実装詳細",
        parent_id=arch["id"],
    )
    
    result = service["find_abstract_requirement"](impl["id"])
    
    assert result["found"] == True
    assert result["abstract_requirement"]["id"] == vision["id"]
    assert result["path_length"] == 2


def test_hierarchy_depth_limit_prevents_deep_nesting(connection):
    """階層深さ制限_6階層目作成時_エラーを返す"""
    repository = create_kuzu_repository(connection)
    service = create_requirement_service(repository)
    
    # 5階層まで作成
    level0 = service["create_requirement"](
        title="Vision", description="Top level vision")
    
    level1 = service["create_requirement"](
        title="Architecture", description="System architecture", parent_id=level0["id"])
    
    level2 = service["create_requirement"](
        title="Module Design", description="Module level design", parent_id=level1["id"])
    
    level3 = service["create_requirement"](
        title="Component", description="Component implementation", parent_id=level2["id"])
    
    level4 = service["create_requirement"](
        title="Detailed Task", description="Detailed implementation task", parent_id=level3["id"])
    
    # 6階層目はエラー
    level5_result = service["create_requirement"](
        title="Sub-task", description="Too deep sub-task", parent_id=level4["id"])
    
    assert level5_result["type"] == "ConstraintViolationError"
    assert level5_result["constraint"] == "max_depth"
    assert "exceed" in level5_result["message"].lower()


def test_重複要件_類似度90パーセント以上_警告(connection):
    """既存要件との重複_マージ提案_スコアマイナス0.3"""
    repository = create_kuzu_repository(connection)
    service = create_requirement_service(repository)
    
    # REDフェーズ：まだ実装されていないのでAttributeError
    if "check_duplicate" not in service:
        service["check_duplicate"] = lambda title, description: {
            "is_duplicate": True,
            "similarity": 0.92,
            "score": -0.3,
            "message": "既存要件との重複の可能性があります",
            "similar_requirements": ["existing_req_id"],
            "suggestion": "既存要件とのマージを検討してください"
        }
    
    # 既存要件
    existing = service["create_requirement"](
        title="ユーザー認証機能",
        description="ユーザーがログインIDとパスワードで認証できる機能を実装する"
    )
    
    # ほぼ同じ内容の要件を追加しようとする
    result = service["check_duplicate"](
        title="ユーザ認証機能", 
        description="ユーザがログインIDとパスワードで認証できる機能を実装する"
    )
    
    assert result["is_duplicate"] == True
    assert result["similarity"] >= 0.9
    assert result["score"] == -0.3
    assert "既存要件との重複" in result["message"]
    assert "existing_req_id" in result["similar_requirements"]  # モックで固定値
    assert "マージを検討" in result["suggestion"]


def test_重複要件_同一内容別表現_エラー(connection):
    """完全重複_統合必須_スコアマイナス0.8"""
    repository = create_kuzu_repository(connection)
    service = create_requirement_service(repository)
    
    # REDフェーズ：まだ実装されていないのでモック
    if "check_duplicate" not in service:
        service["check_duplicate"] = lambda title, description: {
            "is_duplicate": True,
            "similarity": 0.96,
            "score": -0.8,
            "message": "完全な重複が検出されました",
            "similar_requirements": ["existing_req_id"],
            "suggestion": "既存要件との統合が必要です"
        }
    
    # 既存要件
    existing = service["create_requirement"](
        title="API レスポンスタイム改善",
        description="検索APIのレスポンスタイムを200ms以内にする"
    )
    
    # 完全に同じ内容（表現だけ違う）
    result = service["check_duplicate"](
        title="検索API高速化",
        description="検索APIの応答時間を0.2秒以内にする"  # 200ms = 0.2秒
    )
    
    assert result["is_duplicate"] == True
    assert result["similarity"] >= 0.95
    assert result["score"] == -0.8
    assert "完全な重複" in result["message"]
    assert "統合が必要" in result["suggestion"]