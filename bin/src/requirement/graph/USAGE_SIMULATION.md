# requirement/graph 使用シミュレーション

## ペルソナ1: 田中（シニアエンジニア）
- **役割**: テックリード、アーキテクチャ設計担当
- **経験**: KuzuDB使用経験あり、グラフDB精通
- **目的**: 新規プロジェクトの要件管理システム構築

## ペルソナ2: 鈴木（ジュニアエンジニア）  
- **役割**: 実装担当、要件入力作業
- **経験**: RDB経験のみ、グラフDB初心者
- **目的**: 要件の登録と検索機能の利用

---

## Day 1: 初期セットアップ

### 田中（9:00）
```bash
# プロジェクトのクローンと環境確認
git clone https://github.com/company/requirement-graph
cd requirement/graph

# README確認
cat README.md
# "要件管理のグラフデータベースか。VSS/FTSで重複検出もできるのか"

# 開発環境の構築
nix develop
# "お、Nixで環境が統一されてる。いいね"
```

### 鈴木（9:30）
```bash
# 田中さんからの指示でセットアップ
cd requirement/graph
nix develop
# "nix develop...？初めて見るコマンドだ"

# エラー
# "error: experimental Nix feature 'flakes' is disabled"
# 田中さんに聞こう...
```

### 田中（9:45）
```bash
# 鈴木のサポート
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf

# 動作確認
nix develop -c python --version
# "Python 3.12.5、OK"

# DB初期化
python -m requirement.graph init
# "Applying DDL schema version 3.4.0..."
```

---

## Day 2: 要件登録の実装

### 鈴木（10:00）
```bash
# ドキュメントを読む
cat HOW_TO_TEST.md
# "テストはnix develop -c pytestか..."

# 既存のテストを確認
nix develop -c pytest -m "not slow" -v
# "81 passed, 1 failed...まあまあ動いてる"

# 要件登録を試してみる
python
>>> from requirement.graph.infrastructure.database_factory import create_connection
>>> from requirement.graph.infrastructure.kuzu_repository import KuzuRepository
>>> conn = create_connection("./test.db")
# "エラー...どうやって使うんだ？"
```

### 田中（10:30）
```bash
# コード例を見せる
cat application/search_adapter.py
# "ああ、SearchAdapterを使えばいいのか"

# 実際の使用例を作成
cat > usage_example.py << 'EOF'
from requirement.graph.application.search_adapter import SearchAdapter
from requirement.graph.infrastructure.database_factory import create_connection

# DB接続
conn = create_connection("./requirements.db")
adapter = SearchAdapter("./requirements.db", conn)

# 要件追加
requirement = {
    "id": "REQ-001",
    "title": "ユーザー認証機能",
    "description": "メールアドレスとパスワードでログインできる"
}

# 重複チェック
duplicates = adapter.check_duplicates(
    f"{requirement['title']} {requirement['description']}", 
    threshold=0.7
)

if not duplicates:
    adapter.add_to_index(requirement)
    print("要件を登録しました")
else:
    print(f"類似要件が見つかりました: {duplicates[0]['id']}")
EOF

python usage_example.py
```

---

## Day 3: 依存関係の管理

### 田中（11:00）
```bash
# Cypherクエリを確認
ls query/dml/
# "add_dependency.cypherがあるな"

cat query/dml/add_dependency.cypher
# "MATCH節で両方のノードを確認してからCREATEか、いいね"

# 依存関係追加の実装
cat > add_dependencies.py << 'EOF'
from requirement.graph.infrastructure.database_factory import create_connection
from requirement.graph.query.loader import QueryLoader

conn = create_connection("./requirements.db")
loader = QueryLoader("./query")

# 依存関係を追加
query = loader.load_query("dml/add_dependency")
conn.execute(query, {
    "from_id": "REQ-002",  # 認証API
    "to_id": "REQ-001",    # ユーザー認証機能
    "timestamp": "2024-01-15T10:00:00Z"
})
print("依存関係を追加しました")
EOF
```

### 鈴木（14:00）
```bash
# 依存関係の可視化を試みる
cat query/dql/find_dependencies.cypher
# "うーん、Cypherクエリ難しい..."

# 田中さんのヘルプで実装
python
>>> from requirement.graph.infrastructure.database_factory import create_connection
>>> conn = create_connection("./requirements.db")
>>> result = conn.execute("""
    MATCH (r:Requirement {id: 'REQ-002'})-[:DEPENDS_ON*]->(dep:Requirement)
    RETURN dep.id, dep.title
""")
>>> for row in result:
...     print(f"依存: {row['dep.id']} - {row['dep.title']}")
```

---

## Day 4: 重複検出の活用

### 鈴木（10:00）
```bash
# 新しい要件を登録しようとする
cat > new_requirement.py << 'EOF'
from requirement.graph.application.search_adapter import SearchAdapter

adapter = SearchAdapter("./requirements.db")

# 似たような要件を登録しようとする
new_req = {
    "id": "REQ-010", 
    "title": "ログイン機能",
    "description": "ユーザーがメールとパスワードで認証できるようにする"
}

# 重複チェック
text = f"{new_req['title']} {new_req['description']}"
duplicates = adapter.check_duplicates(text, threshold=0.6)

for dup in duplicates:
    print(f"類似度 {dup['score']:.2f}: {dup['id']} - {dup['title']}")
EOF

python new_requirement.py
# "類似度 0.85: REQ-001 - ユーザー認証機能"
# "おお！ちゃんと検出された！"
```

### 田中（15:00）
```bash
# パフォーマンステスト
cat > performance_test.py << 'EOF'
import time
from requirement.graph.application.search_adapter import SearchAdapter

adapter = SearchAdapter("./requirements.db")

# 1000件の要件で検索性能をテスト
start = time.time()
results = adapter.search_hybrid("認証 セキュリティ", k=20)
end = time.time()

print(f"検索時間: {end - start:.3f}秒")
print(f"結果件数: {len(results)}")
EOF

python performance_test.py
# "検索時間: 0.082秒"
# "VSS/FTSの組み合わせ、速いな"
```

---

## Day 5: 本番環境への展開準備

### 田中（10:00）
```bash
# 環境変数の確認
cat infrastructure/variables/env.py
# "RGL_で始まる環境変数か"

# 本番用設定
export RGL_DB_PATH=/data/requirements/prod.db
export RGL_LOG_LEVEL=INFO

# マイグレーション戦略の確認
cat TO_ARCHITECTURE.md
# "DDL/DML/DQL分離の計画があるのか。将来性も考えられてる"

# E2Eテストの実行
nix develop -c pytest -m e2e -v
# "E2Eテストは時間かかるな...でも網羅的だ"
```

### 鈴木（14:00）
```bash
# ドキュメント作成
cat > USER_GUIDE.md << 'EOF'
# requirement/graph 利用ガイド

## 基本的な使い方

### 1. 要件の登録
```python
from requirement.graph.application.search_adapter import SearchAdapter

adapter = SearchAdapter("./requirements.db")
requirement = {
    "id": "REQ-XXX",
    "title": "要件タイトル",
    "description": "要件の詳細説明"
}

# 重複チェックしてから登録
if not adapter.check_duplicates(f"{requirement['title']} {requirement['description']}"):
    adapter.add_to_index(requirement)
```

### 2. 要件の検索
```python
# キーワード検索
results = adapter.search_keyword("認証")

# 類似検索
results = adapter.search_similar("ユーザーログイン機能を実装")

# ハイブリッド検索（推奨）
results = adapter.search_hybrid("認証 セキュリティ")
```
EOF

# 田中さんに確認してもらう
```

---

## 振り返り

### 田中の感想
- **良い点**:
  - Nixによる環境構築が簡単
  - VSS/FTSの統合が優秀
  - グラフDBの利点が活かされている
  - テストが充実している

- **改善点**:
  - 初期設定の自動化があるとよい
  - Cypher初心者向けのヘルパー関数が欲しい
  - Web UIがあれば非エンジニアも使える

### 鈴木の感想
- **良い点**:
  - 重複検出が実用的で便利
  - SearchAdapterが使いやすい
  - エラーメッセージが分かりやすい

- **困った点**:
  - Nix/Cypherの学習曲線が急
  - グラフDBの概念理解に時間がかかった
  - 可視化ツールが欲しい

## 実際の成果

5日間で実現できたこと：
1. ✅ 要件管理システムの基本構築
2. ✅ 50件の要件登録と依存関係設定  
3. ✅ 重複検出による品質向上（3件の重複を防止）
4. ✅ 検索機能による既存要件の活用
5. ✅ チーム内での知識共有とドキュメント作成

このシステムにより、要件の重複を防ぎ、依存関係を明確化することで、プロジェクトの要件管理が大幅に改善された。