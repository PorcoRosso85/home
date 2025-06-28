# 🚨 重大なバグ：履歴機能が偽の結果を返している

## 問題の詳細

`kuzu_repository.py`の`get_requirement_history()`実装（509-524行）:

```python
MATCH (r:RequirementEntity {id: $req_id})-[:HAS_VERSION]->(v:VersionState)
RETURN r.id as requirement_id,
       r.title as title,           # ← 常に現在のタイトル！
       r.description as description, # ← 常に現在の説明！
       r.status as status,         # ← 常に現在のステータス！
       r.priority as priority,     # ← 常に現在の優先度！
       v.id as version_id,
       v.timestamp as timestamp,
       ...
```

## 何が起きているか

例：要件が3回更新された場合
- v1: title="ログイン機能", status="proposed"
- v2: title="OAuth認証", status="approved"
- v3: title="SSO対応", status="implemented"

**期待される履歴**:
```
[
  {version: "v1", title: "ログイン機能", status: "proposed"},
  {version: "v2", title: "OAuth認証", status: "approved"},
  {version: "v3", title: "SSO対応", status: "implemented"}
]
```

**実際に返される履歴**:
```
[
  {version: "v1", title: "SSO対応", status: "implemented"}, # 現在の値！
  {version: "v2", title: "SSO対応", status: "implemented"}, # 現在の値！
  {version: "v3", title: "SSO対応", status: "implemented"}  # 現在の値！
]
```

## 影響

1. **監査証跡として使えない** - 過去の状態が分からない
2. **変更追跡が不可能** - 何がいつ変わったか分からない
3. **コンプライアンス違反** - 履歴保持要件を満たせない
4. **ユーザーの信頼失墜** - 履歴機能が嘘をつく

## 根本原因

- RequirementEntityがミュータブル（更新される）設計
- 過去の状態を保存する仕組みがない
- RequirementSnapshotが削除されたが、代替実装がない

## 緊急度: 🔴 **最高**

このバグは履歴管理システムの根幹を揺るがす重大な問題です。