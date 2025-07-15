"""
TDD Tests for Directory Scanner with Search
Run with: nix develop -c uv run pytest

規約遵守:
- 1つのテストに1つのアサーション
- テストファーストを厳守
- モックよりも実際の値を使用（in-memory DB）
"""

import pytest
import os
import sys
import tempfile
import time
from typing import Dict, Any

# 型定義インポート
from scanner_types import (
    ScanSuccess,
    ScanError,
    ScanResult,
    DiffSuccess,
    DiffError,
    DiffResult,
    SearchSuccess,
    SearchError,
    SearchResult,
    IndexSuccess,
    IndexError,
    IndexResult,
    MetadataSuccess,
    MetadataError,
    MetadataResult,
    DirectoryInfo,
    DBStatus,
)


# 初期スキャンテスト


def test_初回スキャン_全ディレクトリ検出_永続化成功(test_directory_structure, mock_scanner):
    """初回スキャンで全ディレクトリを検出し永続化する"""
    scanner = mock_scanner(test_directory_structure, ":memory:")
    result = scanner["full_scan"](False, True, False)

    # デバッグ出力
    if not result["ok"]:
        print(f"Error in full_scan: {result}")

    assert result["ok"] is True
    # ディレクトリ構造: temp_dir, poc, auth, search (+ empty, .gitは除外)
    assert result["scanned_count"] >= 3


def test_空ディレクトリ_スキップ_カウント正確(temp_dir, mock_scanner):
    """空ディレクトリはスキップされカウントされない"""
    # 空ディレクトリと非空ディレクトリ
    os.makedirs(f"{temp_dir}/empty")
    os.makedirs(f"{temp_dir}/with_file")
    open(f"{temp_dir}/with_file/test.txt", "w").close()

    scanner = mock_scanner(temp_dir, ":memory:")
    result = scanner["full_scan"](True, True, False)

    assert result["ok"] is True
    assert result["scanned_count"] == 2  # root + with_file


def test_隠しディレクトリ_除外_dot始まり無視(temp_dir, mock_scanner):
    """ドットで始まる隠しディレクトリは除外される"""
    os.makedirs(f"{temp_dir}/.git")
    os.makedirs(f"{temp_dir}/visible")

    scanner = mock_scanner(temp_dir, ":memory:")
    result = scanner["full_scan"](False, True, False)

    assert result["ok"] is True
    assert result["scanned_count"] == 2  # root + visible


# 差分検知テスト


def test_新規ディレクトリ追加_差分検出_インクリメンタル更新():
    """新規ディレクトリ追加時に差分を検出しインクリメンタル更新"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = create_directory_scanner(tmpdir, ":memory:")

        # 初回スキャン
        scanner["full_scan"](False, True, False)

        # 新規ディレクトリ追加
        os.makedirs(f"{tmpdir}/new_feature")

        # 差分検知
        diff_result = scanner["detect_changes"]()

        assert diff_result["ok"] is True
        assert len(diff_result["added"]) == 1
        assert diff_result["added"][0] == f"{tmpdir}/new_feature"


def test_ディレクトリ削除_検出_DBから削除():
    """ディレクトリ削除を検出しDBから削除"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        to_delete = f"{tmpdir}/to_delete"
        os.makedirs(to_delete)

        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, False)

        # ディレクトリ削除
        os.rmdir(to_delete)

        diff_result = scanner["detect_changes"]()

        assert diff_result["ok"] is True
        # to_deleteディレクトリが削除されたことを確認
        assert any("to_delete" in path for path in diff_result["deleted"])


def test_README追加_既存ディレクトリ_更新検知():
    """既存ディレクトリにREADME追加時に更新を検知"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = f"{tmpdir}/poc"
        os.makedirs(target_dir)

        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, False)

        # README追加
        with open(f"{target_dir}/README.md", "w") as f:
            f.write("# POC Directory")

        diff_result = scanner["detect_changes"]()

        assert diff_result["ok"] is True
        assert target_dir in diff_result["modified"]


@pytest.mark.xfail(reason="README update detection not fully implemented")
def test_README更新_タイムスタンプ変更_再インデックス():
    """README更新時にタイムスタンプ変更を検知し再インデックス"""
    from main import create_directory_scanner
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        readme_path = f"{tmpdir}/README.md"

        # 初期README作成
        with open(readme_path, "w") as f:
            f.write("# Initial")

        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, False)

        # 少し待ってからREADME更新
        time.sleep(0.1)
        with open(readme_path, "w") as f:
            f.write("# Updated")

        diff_result = scanner["detect_changes"]()

        assert diff_result["ok"] is True
        assert tmpdir in diff_result["modified"]


# 永続化とリストアテスト


def test_DB永続化_再起動後_全データ復元():
    """DB永続化後、再起動しても全データが復元される"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test.db"

        # 初回スキャンと永続化
        scanner1 = create_directory_scanner(tmpdir, db_path)
        scan_result = scanner1["full_scan"](False, True, False)
        initial_count = scan_result["scanned_count"]

        # 新しいインスタンスで復元
        scanner2 = create_directory_scanner(tmpdir, db_path)
        status = scanner2["get_status"]()

        assert status["total_directories"] == initial_count


@pytest.mark.xfail(reason="FTS not implemented yet")
def test_インデックス保持_FTS事前構築_高速検索可能():
    """FTSインデックスが保持され高速検索可能"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        # READMEを持つディレクトリ作成
        os.makedirs(f"{tmpdir}/auth")
        with open(f"{tmpdir}/auth/README.md", "w") as f:
            f.write("Authentication module")

        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, False)
        scanner["build_fts_index"]()

        # FTS検索
        search_result = scanner["search_fts"]("authentication")

        assert search_result["ok"] is True
        assert search_result["total"] > 0


@pytest.mark.xfail(reason="VSS embeddings not implemented yet")
def test_VSS埋め込み保存_再計算不要_メモリ効率():
    """VSS埋め込みが保存され再計算不要"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test.db"

        # 埋め込み生成を伴うスキャン
        scanner1 = create_directory_scanner(tmpdir, db_path)
        scanner1["full_scan"](False, True, True)

        # 再起動後、埋め込みが保持されているか確認
        scanner2 = create_directory_scanner(tmpdir, db_path)
        has_embeddings = scanner2["check_embeddings"]()

        assert has_embeddings is True


# 検索機能テスト


@pytest.mark.xfail(reason="FTS not implemented yet")
def test_FTS検索_キーワード一致_高速応答():
    """FTSでキーワード一致を高速検索"""
    from main import create_directory_scanner
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        # 複数のREADME作成
        for name in ["auth", "search", "cache"]:
            os.makedirs(f"{tmpdir}/{name}")
            with open(f"{tmpdir}/{name}/README.md", "w") as f:
                f.write(f"# {name.capitalize()} Module")

        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, False)
        scanner["build_fts_index"]()

        # 検索実行
        start = time.time()
        result = scanner["search_fts"]("cache")
        duration = time.time() - start

        assert result["ok"] is True
        assert result["duration_ms"] < 100  # 100ms以内


@pytest.mark.xfail(reason="VSS not implemented yet")
def test_VSS検索_意味的類似_関連POC発見():
    """VSSで意味的に類似した関連POCを発見"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        # 認証関連のディレクトリ
        auth_dirs = ["oauth", "jwt", "session"]
        for name in auth_dirs:
            os.makedirs(f"{tmpdir}/{name}")
            with open(f"{tmpdir}/{name}/README.md", "w") as f:
                f.write(f"# {name.upper()} Authentication")

        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, True)

        # "ログイン"で検索（認証と意味的に類似）
        result = scanner["search_vss"]("login system", k=3)

        assert result["ok"] is True
        assert len(result["hits"]) > 0


@pytest.mark.xfail(reason="Hybrid search not implemented yet")
def test_ハイブリッド検索_両方組み合わせ_ランキング統合():
    """FTSとVSSを組み合わせたハイブリッド検索"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, True)
        scanner["build_fts_index"]()

        # ハイブリッド検索
        result = scanner["search_hybrid"]("authentication", alpha=0.5)

        assert result["ok"] is True
        assert "fts_weight" in result  # ハイブリッドスコア情報


# メタデータ抽出テスト


def test_README無し_コードdocstring抽出_自動説明生成():
    """README無しでもコードのdocstringから説明を抽出"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(f"{tmpdir}/utils")
        with open(f"{tmpdir}/utils/main.py", "w") as f:
            f.write('"""Utility functions for data processing"""\n')

        scanner = create_directory_scanner(tmpdir, ":memory:")
        metadata = scanner["extract_metadata"](f"{tmpdir}/utils")

        assert metadata["ok"] is True
        assert metadata["source"] == "docstring"
        assert "data processing" in metadata["description"]


def test_flake_nix_description取得_メタデータ統合():
    """flake.nixのdescriptionフィールドを取得"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/flake.nix", "w") as f:
            f.write('{\n  description = "Test POC for search";\n}')

        scanner = create_directory_scanner(tmpdir, ":memory:")
        metadata = scanner["extract_metadata"](tmpdir)

        assert metadata["ok"] is True
        assert metadata["source"] == "flake"
        assert metadata["description"] == "Test POC for search"


def test_package_json_description参照_Node対応():
    """package.jsonのdescriptionを参照"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/package.json", "w") as f:
            f.write('{"description": "Node.js search module"}')

        scanner = create_directory_scanner(tmpdir, ":memory:")
        metadata = scanner["extract_metadata"](tmpdir)

        assert metadata["ok"] is True
        assert metadata["source"] == "package.json"


# パフォーマンステスト


@pytest.mark.timeout(5)
def test_1000ディレクトリ_5秒以内_初回スキャン完了():
    """1000ディレクトリを5秒以内にスキャン"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1000ディレクトリ作成
        for i in range(1000):
            os.makedirs(f"{tmpdir}/dir_{i:04d}")

        scanner = create_directory_scanner(tmpdir, ":memory:")
        result = scanner["full_scan"](False, True, False)

        assert result["ok"] is True
        assert result["duration_ms"] < 5000


@pytest.mark.timeout(1)
def test_インクリメンタル更新_100ms以内_差分のみ処理():
    """差分のみの処理を100ms以内に完了"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        # 初期状態
        for i in range(100):
            os.makedirs(f"{tmpdir}/dir_{i:03d}")

        scanner = create_directory_scanner(tmpdir, ":memory:")
        scanner["full_scan"](False, True, False)

        # 1つだけ追加
        os.makedirs(f"{tmpdir}/new_dir")

        # 差分更新
        result = scanner["incremental_update"]()

        assert result["ok"] is True
        assert result["duration_ms"] < 100


# エラーハンドリングテスト


def test_権限エラー_スキップ_他は継続():
    """権限エラーのディレクトリはスキップし他は継続"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        # 通常ディレクトリ
        os.makedirs(f"{tmpdir}/normal")

        # 権限なしディレクトリ（シミュレート）
        restricted = f"{tmpdir}/restricted"
        os.makedirs(restricted)
        os.chmod(restricted, 0o000)

        try:
            scanner = create_directory_scanner(tmpdir, ":memory:")
            result = scanner["full_scan"](False, True, False)

            assert result["ok"] is True
            assert result["scanned_count"] >= 1  # 少なくとも通常ディレクトリ
        finally:
            # クリーンアップ
            os.chmod(restricted, 0o755)


def test_壊れたシンボリックリンク_無視_クラッシュしない():
    """壊れたシンボリックリンクを無視しクラッシュしない"""
    from main import create_directory_scanner

    with tempfile.TemporaryDirectory() as tmpdir:
        # 壊れたシンボリックリンク作成
        os.symlink("/nonexistent/path", f"{tmpdir}/broken_link")

        scanner = create_directory_scanner(tmpdir, ":memory:")
        result = scanner["full_scan"](False, True, False)

        assert result["ok"] is True


# CLI関連テスト


def test_環境変数未設定_エラーメッセージ_必須変数():
    """必須環境変数が未設定の場合にエラーメッセージ"""
    from infrastructure.variables.env import validate_environment

    # 環境変数を一時的にクリア
    old_env = os.environ.copy()
    os.environ.clear()

    try:
        errors = validate_environment()
        assert "DIRSCAN_ROOT_PATH" in errors
        assert "DIRSCAN_DB_PATH" in errors
    finally:
        # 環境変数を復元
        os.environ.update(old_env)


def test_CLI実行_引数パース_コマンド分岐():
    """CLI実行時の引数パースとコマンド分岐"""
    from cli import create_cli_parser

    parser = create_cli_parser()

    # scanコマンド
    args = parser.parse_args(["scan"])
    assert args.command == "scan"

    # searchコマンド
    args = parser.parse_args(["search", "query"])
    assert args.command == "search"
    assert args.query == "query"
