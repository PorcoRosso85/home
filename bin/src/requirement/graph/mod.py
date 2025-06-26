"""
Requirement Graph Logic - 公開API

開発決定事項を管理し、類似性検索を提供するツール

## 使用例

### Python APIとして使用:
```python
from requirement.graph import create_rgl_service

# サービス作成
service = create_rgl_service()

# 決定事項を追加
result = service["add_decision"](
    title="KuzuDB移行",
    description="関係性クエリを可能にするためJSONLからKuzuDBへ移行",
    tags=["architecture", "L1"]
)

# 類似検索
similar = service["search_similar"]("データベース移行", threshold=0.5)
for decision in similar:
    print(f"{decision['id']}: {decision['title']}")
```

### CLIとして使用:
```bash
# 決定事項を追加
python -m requirement.graph add "KuzuDB移行" "関係性クエリを可能にする" --tags architecture L1

# 検索
python -m requirement.graph search "データベース"

# 一覧表示
python -m requirement.graph list --tag architecture
```

依存: なし（純粋Python実装）
"""
import os
from typing import Optional

# Domain exports
from .domain.types import (
    Decision,
    DecisionError,
    DecisionResult,
    DecisionNotFoundError,
    InvalidDecisionError,
    EmbeddingError
)
from .domain.decision import create_decision, calculate_similarity
from .domain.embedder import create_embedding

# Application exports  
from .application.decision_service import create_decision_service

# Infrastructure exports
from .infrastructure.jsonl_repository import create_jsonl_repository
from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.cli_adapter import create_cli


def create_rgl_service(repository_path: Optional[str] = None, use_kuzu: bool = True):
    """
    RGLサービスを作成（便利関数）
    
    Args:
        repository_path: データベースパス
        use_kuzu: KuzuDBを使用するか（デフォルト: True）
        
    Returns:
        DecisionService関数の辞書
    """
    if use_kuzu:
        if repository_path is None:
            repository_path = os.path.expanduser("~/.rgl/graph.db")
        repository = create_kuzu_repository(repository_path)
    else:
        if repository_path is None:
            repository_path = os.path.expanduser("~/.rgl/decisions.jsonl")
        repository = create_jsonl_repository(repository_path)
    
    return create_decision_service(repository)


# CLI実行
if __name__ == "__main__":
    cli = create_cli()
    cli()


# Test cases
def test_public_api_integration_workflow_returns_expected_results():
    """public_api_統合ワークフロー_期待する結果を返す"""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name
    
    try:
        # サービス作成
        service = create_rgl_service(temp_path)
        
        # 決定事項追加
        result1 = service["add_decision"](
            title="GraphDB導入",
            description="関係性を効率的に管理するため",
            tags=["database", "architecture"]
        )
        assert "type" not in result1
        
        result2 = service["add_decision"](
            title="KuzuDB選定",
            description="軽量で高速なグラフDBとして選択",
            tags=["database", "decision"]
        )
        assert "type" not in result2
        
        # 類似検索
        similar = service["search_similar"]("グラフデータベース", threshold=0.3)
        assert len(similar) >= 1
        assert any("Graph" in d["title"] or "Kuzu" in d["title"] for d in similar)
        
        # タグ検索
        by_tag = service["list_by_tag"]("database")
        assert len(by_tag) == 2
        
        print("Public API test passed!")
        
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # CLI mode
        cli = create_cli()
        cli()
    else:
        # Test mode
        test_public_api_integration_workflow_returns_expected_results()