# requirement/graph Flake実使用デモ

## 実際のFlakeコマンドを使った要件管理システム構築

### 1. 初期セットアップ

```bash
# 開発環境に入る
$ nix develop
Requirement Graph Logic (RGL) Development Environment
Environment ready!

# Pythonとパッケージの確認
$ python --version
Python 3.12.5

$ python -c "import kuzu; print(f'KuzuDB: {kuzu.__version__}')"
KuzuDB: 0.6.0

$ python -c "import vss_kuzu; print('VSS module: OK')"
VSS module: OK

$ python -c "import fts_kuzu; print('FTS module: OK')"
FTS module: OK
```

### 2. データベース初期化

```bash
# 初期化（flakeのinitアプリを使用）
$ nix run .#init
{"type": "init", "action": "apply", "create_test_data": true}
Applying DDL schema version 3.4.0...
✅ Schema applied successfully
✅ Test data created

# 再実行時の挙動
$ nix run .#init
ℹ️  データベースは既に存在します: ./rgl_db
再初期化する場合は、データベースディレクトリを削除してから実行してください
  rm -rf ./rgl_db
```

### 3. テストの実行

```bash
# 全テストの実行
$ nix run .#test
========================== test session starts ==========================
collected 126 items

# 高速テストのみ（E2E以外）
$ nix run .#test -- -m "not slow"
========================== test session starts ==========================
collected 126 items / 43 deselected / 83 selected

test_database_factory.py::TestDatabaseFactory::test_create_database PASSED
test_memory_isolation.py::test_connection_isolation PASSED
test_constraints.py::test_requirement_id_format PASSED
...
=================== 82 passed, 1 skipped in 2.19s ====================

# 特定のテストファイルのみ
$ nix run .#test -- application/test_search_adapter.py -v
test_search_adapter.py::TestSearchAdapter::test_initialization PASSED
test_search_adapter.py::TestSearchAdapter::test_check_duplicates PASSED
```

### 4. アプリケーションの実行

```bash
# 対話モード（JSON入力）
$ echo '{"action": "search", "query": "認証", "type": "hybrid"}' | nix run .#run
{
  "status": "success",
  "results": [
    {
      "id": "REQ-001",
      "title": "ユーザー認証機能",
      "score": 0.95
    }
  ]
}

# 要件の追加
$ cat > add_requirement.json << EOF
{
  "action": "add",
  "requirement": {
    "id": "REQ-100",
    "title": "二要素認証",
    "description": "SMSまたはTOTPによる追加認証"
  }
}
EOF

$ cat add_requirement.json | nix run .#run
{
  "status": "success",
  "message": "Requirement REQ-100 added successfully",
  "duplicates_checked": true
}
```

### 5. 開発作業

```bash
# 開発環境で作業
$ nix develop

# Lintの実行
$ nix run .#lint
🔍 Running linters...
✅ All checks passed!

# コードの修正後、テスト実行
$ pytest application/test_search_adapter.py::TestSearchAdapter::test_check_duplicates -v
```

### 6. パッケージとしての利用

```bash
# 別プロジェクトのflake.nixで利用
# flake.nix
{
  inputs = {
    requirement-graph.url = "path:../requirement/graph";
  };
  
  outputs = { self, requirement-graph, ... }: {
    # requirement-graphのPythonパッケージを利用
    devShells.default = pkgs.mkShell {
      buildInputs = [
        requirement-graph.packages.${system}.pythonEnv
      ];
    };
  };
}
```

### 7. 実践的な使用例

```bash
# プロジェクトで実際に使う
$ nix develop

# Pythonスクリプトで要件管理
$ cat > manage_requirements.py << 'EOF'
#!/usr/bin/env python
from requirement.graph.application.search_adapter import SearchAdapter
from requirement.graph.infrastructure.database_factory import create_connection
import json
import sys

def main():
    # DB接続
    conn = create_connection("./project_requirements.db")
    adapter = SearchAdapter("./project_requirements.db", conn)
    
    # コマンドライン引数で動作を分岐
    if len(sys.argv) < 2:
        print("Usage: manage_requirements.py [add|search|check] ...")
        return
    
    command = sys.argv[1]
    
    if command == "add":
        req = json.loads(sys.argv[2])
        # 重複チェック
        text = f"{req['title']} {req.get('description', '')}"
        duplicates = adapter.check_duplicates(text, threshold=0.7)
        
        if duplicates:
            print(f"⚠️  類似要件が見つかりました:")
            for dup in duplicates:
                print(f"  - {dup['id']}: {dup['title']} (類似度: {dup['score']:.2f})")
        else:
            adapter.add_to_index(req)
            print(f"✅ 要件 {req['id']} を追加しました")
    
    elif command == "search":
        query = sys.argv[2]
        results = adapter.search_hybrid(query, k=10)
        print(f"検索結果 ({len(results)}件):")
        for r in results:
            print(f"  - {r['id']}: {r['title']} (スコア: {r.get('score', 0):.2f})")
    
    elif command == "check":
        text = sys.argv[2]
        duplicates = adapter.check_duplicates(text, threshold=0.6)
        if duplicates:
            print("重複の可能性:")
            for dup in duplicates:
                print(f"  - {dup['id']}: {dup['title']} (類似度: {dup['score']:.2f})")
        else:
            print("✅ 重複なし")

if __name__ == "__main__":
    main()
EOF

$ chmod +x manage_requirements.py

# 使用例
$ ./manage_requirements.py add '{"id": "FEAT-001", "title": "ダッシュボード機能", "description": "統計情報を表示"}'
✅ 要件 FEAT-001 を追加しました

$ ./manage_requirements.py search "ダッシュボード"
検索結果 (1件):
  - FEAT-001: ダッシュボード機能 (スコア: 0.98)

$ ./manage_requirements.py check "管理画面で統計を見る機能"
重複の可能性:
  - FEAT-001: ダッシュボード機能 (類似度: 0.72)
```

### 8. CI/CDでの利用

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: DeterminateSystems/nix-installer-action@v4
    - uses: DeterminateSystems/magic-nix-cache-action@v2
    
    # テスト実行
    - name: Run tests
      run: nix run .#test -- -m "not slow"
    
    # Lint
    - name: Run lint
      run: nix run .#lint
```

## Flakeの利点

1. **再現可能な環境**: `nix develop`で全員が同じ環境
2. **依存関係の明確化**: VSS/FTS/KuzuDBが自動的に利用可能
3. **簡単なコマンド**: `nix run .#init`, `nix run .#test`など
4. **CI/CD統合**: GitHub ActionsでもローカルでもNix同じコマンド
5. **パッケージ化**: 他のプロジェクトから`requirement-graph`を簡単に利用可能