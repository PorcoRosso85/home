"""Test VSS integration for flake exploration."""

import tempfile
from pathlib import Path

from flake_graph.vss_adapter import create_flake_document, search_similar_flakes
from flake_graph.scanner import scan_readme_content


def test_flake_document_creation():
    """flake情報からVSS用ドキュメントを作成できる"""
    flake_info = {
        "path": Path("/home/nixos/bin/src/persistence/kuzu_py"),
        "description": "KuzuDB thin wrapper for Python",
        "readme_content": "KuzuDBのNixパッケージを提供..."
    }
    
    doc = create_flake_document(flake_info)
    
    assert doc["id"] == "persistence/kuzu_py"
    assert "KuzuDB thin wrapper" in doc["content"]
    assert "KuzuDBのNixパッケージ" in doc["content"]


def test_scan_readme_content():
    """flakeディレクトリからREADMEを読み込める"""
    with tempfile.TemporaryDirectory() as tmpdir:
        flake_dir = Path(tmpdir) / "test_flake"
        flake_dir.mkdir()
        
        readme = flake_dir / "README.md"
        readme.write_text("# Test Flake\n\nThis is a test flake.")
        
        content = scan_readme_content(flake_dir)
        
        assert content == "# Test Flake\n\nThis is a test flake."


def test_search_flakes_by_similarity():
    """類似度でflakeを検索できる"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.kuzu"
        
        # VSSにflake情報をインデックス
        flakes = [
            {"id": "persistence/kuzu_py", "content": "KuzuDB wrapper for Python グラフデータベース"},
            {"id": "telemetry/log_py", "content": "Logging library for Python ロギング"}
        ]
        
        # 検索実行 - キーワード検索で"データベース"を検索
        results = search_similar_flakes(
            query="グラフデータベース",
            flakes=flakes,
            db_path=str(db_path),
            limit=5
        )
        
        assert len(results) > 0
        assert results[0]["id"] == "persistence/kuzu_py"
        assert results[0]["score"] > 0.5


def test_search_with_actual_vss():
    """実際のVSSでベクトル検索が動作する"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.kuzu"
        
        # テストデータ
        flakes = [
            {"id": "persistence/kuzu_py", "content": "グラフデータベースのKuzuDBをPythonから利用するためのラッパー"},
            {"id": "search/vss_kuzu", "content": "ベクトル類似度検索を提供するKuzuDB拡張"},
            {"id": "telemetry/log_py", "content": "構造化ログ出力のためのPythonライブラリ"}
        ]
        
        # 類似検索 - "データベース検索"に関連するflakeを探す
        results = search_similar_flakes(
            query="データベース検索",
            flakes=flakes,
            db_path=str(db_path),
            limit=2
        )
        
        assert len(results) == 2
        # ベクトル検索では、両方のデータベース関連flakeが上位に来るはず
        result_ids = [r["id"] for r in results]
        assert "persistence/kuzu_py" in result_ids
        assert "search/vss_kuzu" in result_ids