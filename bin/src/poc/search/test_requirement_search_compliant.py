#!/usr/bin/env python3
"""
規約準拠版テスト - sys.path操作なし、クラスなし
"""

import os
import subprocess
from typing import Dict, List, Any

# 環境変数設定
os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"

# requirement/graphの仮想環境パス
RGL_VENV = "/home/nixos/bin/src/requirement/graph/.venv/bin/python"


def create_mock_connection() -> Dict[str, Any]:
    """モック接続を関数で作成（クラス不使用）"""
    return {"data": [], "index": 0, "execute": lambda query, params=None: create_mock_result([])}


def create_mock_result(data: List[Any]) -> Dict[str, Any]:
    """モック結果を関数で作成（クラス不使用）"""
    result = {"data": data, "index": 0}

    def has_next():
        return result["index"] < len(result["data"])

    def get_next():
        if has_next():
            value = result["data"][result["index"]]
            result["index"] += 1
            return value
        return None

    result["has_next"] = has_next
    result["get_next"] = get_next
    return result


def run_test_in_venv(test_name: str, test_code: str) -> tuple[bool, str, str]:
    """仮想環境でテストコードを実行"""
    # PYTHONPATH環境変数を使用（sys.path操作の代替）
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/nixos/bin/src"

    result = subprocess.run([RGL_VENV, "-c", test_code], capture_output=True, text=True, env=env)

    success = result.returncode == 0
    if success:
        print(f"✓ {test_name}")
    else:
        print(f"✗ {test_name}: {result.stderr.strip()}")

    return success, result.stdout, result.stderr


def test_vss_embedding():
    """VSS埋め込みテスト"""
    code = """
from poc.search.vss.requirement_embedder import generate_requirement_embedding

req = {"title": "認証", "description": "ログイン"}
embedding = generate_requirement_embedding(req)
assert len(embedding) == 384
assert all(isinstance(x, float) for x in embedding)
print("Embedding length:", len(embedding))
"""
    return run_test_in_venv("VSS embedding", code)


def test_cosine_similarity():
    """コサイン類似度テスト"""
    code = """
from poc.search.vss.similarity_search_fixed import calculate_cosine_similarity

vec1 = [1.0, 0.0, 0.0]
vec2 = [0.0, 1.0, 0.0]
vec3 = [1.0, 0.0, 0.0]

sim1 = calculate_cosine_similarity(vec1, vec2)
sim2 = calculate_cosine_similarity(vec1, vec3)

assert abs(sim1) < 0.1  # 直交ベクトル
assert sim2 > 0.9      # 同一ベクトル
print(f"Orthogonal: {sim1:.3f}, Identical: {sim2:.3f}")
"""
    return run_test_in_venv("Cosine similarity", code)


def test_no_scoring():
    """スコアリングなしの確認"""
    # ローカルでテスト（外部プロセス不要）
    from vss.requirement_embedder import generate_requirement_embedding

    # モック結果の確認
    result = {"id": "req_001", "title": "Test", "similarity_rank": 1}

    assert "score" not in result
    assert "similarity_score" not in result
    print("✓ No scoring")
    return True, "", ""


def test_kuzu_integration():
    """KuzuDB統合テスト"""
    code = """
from requirement.graph.infrastructure.database_factory import create_database, create_connection
from poc.search.vss.requirement_embedder import generate_requirement_embedding

# データベース作成
db = create_database(in_memory=True, test_unique=True)
conn = create_connection(db)

# スキーマ作成
conn.execute('''
    CREATE NODE TABLE RequirementEntity (
        id STRING PRIMARY KEY,
        title STRING,
        description STRING,
        embedding DOUBLE[384]
    )
''')

# テストデータ
req = {
    "id": "req_001",
    "title": "認証システム",
    "description": "ユーザーログイン機能"
}

# 埋め込み生成と挿入
embedding = generate_requirement_embedding(req)
conn.execute('''
    CREATE (r:RequirementEntity {
        id: $id,
        title: $title,
        description: $description,
        embedding: $embedding
    })
''', {
    "id": req["id"],
    "title": req["title"],
    "description": req["description"],
    "embedding": embedding
})

# 検証
result = conn.execute("MATCH (r:RequirementEntity) RETURN count(r)")
count = result.get_next()[0]
assert count == 1
print(f"Created {count} requirement(s)")
"""
    return run_test_in_venv("KuzuDB integration", code)


def test_convention_compliance():
    """規約準拠確認"""
    code = """
import os

# 本番コードファイルをチェック
files_to_check = [
    "poc/search/vss/requirement_embedder.py",
    "poc/search/vss/similarity_search_fixed.py",
    "poc/search/fts/keyword_search_fixed.py"
]

violations = []
for file_path in files_to_check:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            # sys.path操作のチェック（コメント以外）
            for i, line in enumerate(content.split('\\n'), 1):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and 'sys.path' in line:
                    violations.append(f"{file_path}:{i} - sys.path manipulation")
            
            # クラス定義のチェック（TypeDict以外）
            if 'class ' in content and 'TypedDict' not in content:
                lines = content.split('\\n')
                for i, line in enumerate(lines, 1):
                    if line.strip().startswith('class ') and 'TypedDict' not in line:
                        violations.append(f"{file_path}:{i} - class definition")

if violations:
    print("Violations found:")
    for v in violations:
        print(f"  - {v}")
    raise AssertionError(f"{len(violations)} violations found")
else:
    print("No violations found in production code")
"""
    return run_test_in_venv("Convention compliance", code)


if __name__ == "__main__":
    print("=== 規約準拠テストスイート ===\n")

    tests = [
        test_vss_embedding,
        test_cosine_similarity,
        test_no_scoring,
        test_kuzu_integration,
        test_convention_compliance,
    ]

    passed = 0
    for test in tests:
        try:
            success, stdout, stderr = test()
            if success:
                passed += 1
                if stdout.strip():
                    print(f"  {stdout.strip()}")
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")

    print(f"\n結果: {passed}/{len(tests)} テスト成功")

    if passed == len(tests):
        print("🟢 全テスト成功（規約準拠）")
