# 論理的不整合の分析結果

## 🚨 発見された重大な不整合

### 1. **RequirementSnapshotの幽霊参照**
- **問題**: コードが存在しないRequirementSnapshotを参照
- **影響箇所**:
  - `test_version_service.py`: `snapshot_id`をアサート（98行目）
  - `version_service.py`: `snapshot_id`を返却（132行目）
- **矛盾**: MIGRATION_V4_NOTES.mdによるとRequirementSnapshotは既に削除済み

### 2. **ミュータブル vs イミュータブルの混在**
- **現在の実装**: RequirementEntityを`MERGE`で更新（ミュータブル）
- **新仕様（REDテスト）**: 各更新で新エンティティ作成（イミュータブル）
- **矛盾**: 同じシステム内で両方の動作を期待

### 3. **バージョン管理の二重実装**
- **VersionState**: メタデータのみ（operation、author、changed_fields）
- **VersionEntity**: スキーマに定義されているが未使用
- **矛盾**: どちらが正式なバージョン管理エンティティか不明確

### 4. **get_requirement_history()の嘘**
```python
# 現在の実装（kuzu_repository.py）
MATCH (r:RequirementEntity {id: $req_id})-[:HAS_VERSION]->(v:VersionState)
RETURN r, v  # rは常に現在の状態！
```
- **問題**: 履歴照会なのに現在の状態を繰り返し返す
- **期待**: 各バージョン時点での実際の状態

### 5. **削除要件の扱いの矛盾**
- **新仕様**: 削除後も履歴アクセス可能
- **現実装**: RequirementEntity削除 → 履歴も消失
- **矛盾**: コンプライアンス要件を満たせない

## 📊 影響を受ける既存テスト

### 必ず失敗するテスト
1. `test_version_service.py::test_version_service_track_change_creates_version`
   - `assert "snapshot_id" in result` が失敗

2. `test_version_service.py::test_version_service_history_returns_sorted_versions`
   - モックデータに`snapshot_id`含む

### 結果が信頼できないテスト
1. 履歴関連の全テスト
   - 実際の過去状態ではなく現在状態を検証している

2. 削除関連のテスト
   - 削除後のアクセスをテストしていない

## 🔧 修正の優先順位

### Phase 1: 即座に修正すべき
1. `snapshot_id`への参照を全て削除
2. `get_requirement_history()`を真の履歴を返すよう修正

### Phase 2: アーキテクチャ決定
1. RequirementEntityのイミュータブル化
2. VersionEntityの活用 or 削除

### Phase 3: テストの整合性確保
1. 既存テストを新仕様に合わせて修正
2. REDテストがGREENになるよう実装

## 📋 失敗するテストの詳細分析

### 確実に失敗するテスト

#### 1. `test_version_service.py`
- **`test_version_service_track_change_creates_version`**
  - 行101: `assert "snapshot_id" in result`
  - 理由: snapshot_idは新設計で廃止

#### 2. `test_jsonl_repository.py`
- **`test_jsonl_repository_crud_operations_returns_expected_results`**
  - 行40-43: `update()`メソッドを使用
  - 理由: イミュータブル設計では`update()`は存在しない

### 修正が必要なテスト

#### 1. `test_kuzu_repository.py`
- スキーマに`VersionEntity`を定義しているが未使用
- MERGEによる更新を前提としている

#### 2. `test_requirement_service.py`
- 明示的な衝突はないが、ミュータブル動作を期待している可能性

### 新旧設計の対立

**最大の矛盾**: 
- `test_version_tracking_without_snapshot.py`: **イミュータブル設計を完全に定義**（35テスト）
- その他のテスト: **ミュータブル設計を前提**

これは同じシステムに2つの異なる設計思想が混在していることを示しています。

## 🎯 結論

**現在のシステムには深刻な論理的不整合があります：**

1. **削除されたはずのエンティティへの参照**が残存
2. **履歴機能が偽の結果**を返している
3. **ミュータブル/イミュータブルの設計が混在**
4. **テスト間で相反する期待値**が存在

これらの不整合により、現在のシステムは**真のバージョン管理システムとして機能していません**。

### 推奨アクション

1. **設計の統一**: イミュータブル設計（`test_version_tracking_without_snapshot.py`）を正式採用
2. **既存テストの修正**: 新設計に合わせて全テストを更新
3. **実装の修正**: REDテストがGREENになるよう実装

REDテストは正しい仕様を示していますが、既存の実装・テストとの間に大きなギャップがあります。このギャップを埋めることが、リファクタリング成功の鍵です。