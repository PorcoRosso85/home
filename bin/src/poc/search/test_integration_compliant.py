#!/usr/bin/env python3
"""
統合テスト（規約準拠版）- PYTHONPATH環境変数使用
"""

import os
import subprocess

# 環境設定
RGL_VENV = "/home/nixos/bin/src/requirement/graph/.venv/bin/python"
PROJECT_ROOT = "/home/nixos/bin/src"


def run_integration_test():
    """統合テストを実行"""
    test_script = """
# 必要なインポート
from requirement.graph.infrastructure.database_factory import create_database, create_connection
from poc.search.vss.requirement_embedder import generate_requirement_embedding
from poc.search.vss.similarity_search_fixed import search_similar_requirements_fallback
from poc.search.fts.keyword_search_fixed import search_by_keywords_fallback

print("1. データベース初期化...")
db = create_database(in_memory=True, test_unique=True)
conn = create_connection(db)

print("2. スキーマ作成...")
conn.execute('''
    CREATE NODE TABLE RequirementEntity (
        id STRING PRIMARY KEY,
        title STRING,
        description STRING,
        acceptance_criteria STRING,
        status STRING DEFAULT 'proposed',
        priority UINT8 DEFAULT 1,
        embedding DOUBLE[384]
    )
''')

print("3. テストデータ投入...")
test_requirements = [
    {
        "id": "req_auth_001",
        "title": "ユーザー認証機能",
        "description": "セキュアなログインシステムの実装",
        "acceptance_criteria": "パスワードは8文字以上、英数字混在必須"
    },
    {
        "id": "req_auth_002",
        "title": "二要素認証",
        "description": "追加のセキュリティレイヤーとしてのTOTP実装",
        "acceptance_criteria": "Google Authenticator対応"
    },
    {
        "id": "req_dash_001",
        "title": "管理ダッシュボード",
        "description": "システム状態を可視化するダッシュボード",
        "acceptance_criteria": "リアルタイム更新、レスポンシブデザイン"
    }
]

for req in test_requirements:
    embedding = generate_requirement_embedding(req)
    conn.execute('''
        CREATE (r:RequirementEntity {
            id: $id,
            title: $title,
            description: $description,
            acceptance_criteria: $criteria,
            embedding: $embedding
        })
    ''', {
        "id": req["id"],
        "title": req["title"],
        "description": req["description"],
        "criteria": req["acceptance_criteria"],
        "embedding": embedding
    })

print("\\n4. 類似検索テスト...")
vss_results = search_similar_requirements_fallback(conn, "ログイン認証システム", k=3)
print(f"   検索結果: {len(vss_results)}件")
for r in vss_results:
    print(f"   - [{r['similarity_rank']}] {r['id']}: {r['title']}")

print("\\n5. キーワード検索テスト...")
fts_results = search_by_keywords_fallback(conn, "認証")
print(f"   検索結果: {len(fts_results)}件")
for r in fts_results:
    print(f"   - {r['id']}: {r['title']} (match: {r['match_type']})")

print("\\n6. 統合結果...")
all_ids = set()
all_ids.update(r['id'] for r in vss_results)
all_ids.update(r['id'] for r in fts_results)
print(f"   ユニーク要件数: {len(all_ids)}")

print("\\n✅ 統合テスト完了")
"""

    # 環境変数でPYTHONPATH設定
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    env["RGL_SKIP_SCHEMA_CHECK"] = "true"

    # テスト実行
    result = subprocess.run([RGL_VENV, "-c", test_script], capture_output=True, text=True, env=env)

    print("=== 統合テスト結果 ===")
    print(result.stdout)

    if result.stderr:
        print("\nエラー:")
        print(result.stderr)

    return result.returncode == 0


def check_compliance():
    """規約準拠チェック"""
    print("\n=== 規約準拠チェック ===")

    # チェック対象ファイル
    files_to_check = [
        "vss/requirement_embedder.py",
        "vss/similarity_search.py",
        "vss/similarity_search_fixed.py",
        "fts/keyword_search.py",
        "fts/keyword_search_fixed.py",
        "hybrid/requirement_search_engine.py",
    ]

    violations = []

    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # sys.path チェック（コメント以外）
                    if stripped and not stripped.startswith("#") and "sys.path" in line:
                        violations.append(f"{file_path}:{i} - sys.path manipulation")

                    # クラス定義チェック（TypedDict以外）
                    if stripped.startswith("class ") and "TypedDict" not in line:
                        violations.append(f"{file_path}:{i} - class definition")

    if violations:
        print("❌ 違反が見つかりました:")
        for v in violations:
            print(f"  - {v}")
        return False
    else:
        print("✅ 本番コードは規約準拠")
        return True


if __name__ == "__main__":
    # 規約チェック
    compliant = check_compliance()

    # 統合テスト
    test_passed = run_integration_test()

    # 最終結果
    print("\n=== 最終結果 ===")
    if compliant and test_passed:
        print("🟢 すべてのチェックに合格（規約準拠）")
    else:
        print("🔴 問題があります:")
        if not compliant:
            print("  - 規約違反あり")
        if not test_passed:
            print("  - テスト失敗")
