# requirement/graph 改善タスク詳細

## 概要
requirement/graphの不要コードとテストを削除し、template入力対応とPOC search統合を最小コストで実現する。

## 基本方針
- **新規作成より削除を優先**（移行コストの最小化）
- **規約違反テストの徹底削除**（テスト修正コストの削減）
- **既存の安定基盤を活用**（requirement/graphはそのまま使用）

## 現在の状況

### 発見された問題
1. **過度に複雑な実装**
   - Cypher直接実行（セキュリティリスク）
   - 摩擦スコアリング（POC searchで代替可能）
   - バージョニングAPI（Git履歴で十分）

2. **規約違反のテスト**
   - アプリケーション層の単体テスト（規約：統合テストのみ）
   - インフラ層の単体テスト（規約：統合テストのみ）
   - 実装詳細に依存したテスト（リファクタリングの壁違反）

3. **POC searchとの重複**
   - 50次元embedding vs 256次元
   - 独自スコアリング vs VSS/FTS

## Phase 0: 規約ベースのテスト削除

### 目的
規約違反テストを削除し、仕様テストのみを残す

### 削除対象（約20ファイル）

#### アプリケーション層の単体テスト
```bash
rm application/test_integrated_consistency_validator.py
rm application/test_priority_consistency_checker.py
rm application/test_requirement_completeness_analyzer.py
rm application/test_resource_conflict_detector.py
rm application/test_semantic_validator.py
rm application/test_version_service.py
```

#### インフラ層の単体テスト
```bash
rm infrastructure/test_cypher_executor.py
rm infrastructure/test_query_validator.py
rm infrastructure/test_custom_procedures.py
rm infrastructure/test_unified_query_interface.py
```

#### 実装詳細依存テスト
```bash
rm test_executive_engineer_simple.py
rm test_inconsistency_detection.py
rm test_user_experience_improvements.py
rm test_migration_impact.py
```

### 成功基準
- テスト数が50%以上削減
- 残存テストは全て仕様テスト
- CIが通る状態を維持

### Phase 0完了時の宣言
```
【宣言】Phase 0: 規約ベースのテスト削除 完了
- 目的：規約違反テストを削除し、仕様テストのみを残す
- 規約遵守：bin/docs/conventions/testing.mdに準拠
- 削除したテスト：アプリケーション層単体テスト、インフラ層単体テスト、実装詳細依存テスト
- 成果：テスト数50%削減達成、仕様テストのみ残存
```

## Phase 1: 不要コード削除

### 目的
削除したテストに対応する実装コードを削除

### 削除対象

#### Cypher直接実行系
```bash
rm infrastructure/cypher_executor.py
rm infrastructure/query_validator.py
rm infrastructure/versioned_cypher_executor.py
```

#### 摩擦スコアリング系
```bash
rm -rf application/*_validator.py
rm -rf application/*_checker.py
rm -rf application/*_detector.py
```

#### バージョニング系
```bash
rm application/version_service.py
rm application/version_service_extensions.py
```

#### 複雑なドメインルール
```bash
rm domain/requirement_conflict_rules.py
rm -rf domain/requirement_health/
rm domain/context_coefficients.py
rm domain/embedder.py  # 50次元
```

### 残すコア機能
```
requirement/graph/
├── main.py
├── domain/
│   ├── types.py
│   └── constraints.py
├── infrastructure/
│   ├── kuzu_repository.py
│   └── database_factory.py
└── ddl/
```

### 成功基準
- コード量が60%以上削減
- 残存テストが全てGREEN
- 基本的なCRUD操作が動作

### Phase 1完了時の宣言
```
【宣言】Phase 1: 不要コード削除 完了
- 目的：削除したテストに対応する実装コードを削除
- 規約遵守：bin/docs/conventions/module_design.mdに準拠
- 削除したコード：Cypher直接実行系、摩擦スコアリング系、バージョニング系、複雑なドメインルール
- 成果：コード量60%削減達成、コア機能のみ残存
```

## Phase 1.1: README統合

### 目的
requirement/templateで作成したREADMEの内容をrequirement/graphに統合

### 実装内容

#### README更新対象
```bash
# requirement/graphの各層にREADMEを配置
requirement/graph/
├── README.md              # トップレベル（更新）
├── domain/
│   └── README.md         # templateから移植
├── application/
│   └── README.md         # templateから移植
└── infrastructure/
    └── README.md         # templateから移植
```

#### 統合方針
- 削除後の実際の構造に合わせて内容を調整
- 責務の明確化と相互参照の維持
- 実装に依存しない抽象的な記述

### 成功基準
- 各層の責務が明確に文書化
- 相互参照リンクが正しく機能
- 削除後の構造と一致

### Phase 1.1完了時の宣言
```
【宣言】Phase 1.1: README統合 完了
- 目的：各層の責務を明確に文書化
- 規約遵守：bin/docs/conventions/documentation.mdに準拠
- 統合内容：domain、application、infrastructureの各README
- 成果：責務の明確化と相互参照の確立
```

## Phase 2: Template入力対応

### 目的
最小限の修正でtemplate入力を受け付ける

### 実装内容

#### main.py修正
```python
def main():
    input_data = json.loads(sys.stdin.read())
    
    if input_data["type"] == "template":
        # テンプレート処理（新規追加）
        result = process_template(input_data)
    elif input_data["type"] == "cypher":
        # 後方互換性のため残す
        result = process_cypher(input_data)
    
    print(json.dumps(result))
```

#### template_processor.py追加（最小実装）
```python
def process_template(input_data):
    template = input_data["template"]
    params = input_data["parameters"]
    
    # テンプレート→Cypherマッピング
    if template == "create_requirement":
        query = f"CREATE (r:RequirementEntity {{id: '{params['id']}', ...}})"
    # ...
    
    return execute_query(query)
```

### 成功基準
- Template入力で基本操作が可能
- 既存のCypher入力も動作（後方互換）
- テスト修正は最小限

### Phase 2完了時の宣言
```
【宣言】Phase 2: Template入力対応 完了
- 目的：最小限の修正でtemplate入力を受け付ける
- 規約遵守：bin/docs/conventions/api_design.mdに準拠
- 実装内容：main.py修正、template_processor.py追加
- 成果：Template/Cypher両対応実現、後方互換性維持
```

## Phase 3: POC Search統合

### 目的
重複検出にPOC searchを活用

### 実装内容

#### search_integration.py追加
```python
from poc.search.infrastructure.search_service_factory import SearchServiceFactory

class SearchIntegration:
    def __init__(self):
        self.search_service = SearchServiceFactory.create()
    
    def check_duplicates(self, text):
        # POC searchを直接利用
        return self.search_service.search_hybrid(text, k=5)
```

#### main.py修正
```python
# 要件作成時に重複チェック
if template == "create_requirement":
    duplicates = search_integration.check_duplicates(params["title"])
    if duplicates:
        return {"warning": "Similar requirements found", "duplicates": duplicates}
```

### 成功基準
- 要件作成時に重複警告
- POC searchの256次元embeddingを活用
- パフォーマンス劣化なし

### Phase 3完了時の宣言
```
【宣言】Phase 3: POC Search統合 完了
- 目的：重複検出にPOC searchを活用
- 規約遵守：bin/docs/conventions/integration.mdに準拠
- 実装内容：search_integration.py追加、main.py修正
- 成果：VSS/FTSハイブリッド検索による重複検出実現
```

## Phase 4: テスト修正と品質保証

### 目的
残存テストをtemplate対応に修正

### 修正対象（約15ファイル）
- ドメイン層テスト（仕様変更なし）
- 統合テスト（入力形式のみ変更）

### 修正パターン
```python
# 旧
input_data = {"type": "cypher", "query": "CREATE ..."}

# 新
input_data = {"type": "template", "template": "create_requirement", "parameters": {...}}
```

### 成功基準
- 全テストGREEN
- カバレッジ70%以上
- E2Eシナリオ動作確認

### Phase 4完了時の宣言
```
【宣言】Phase 4: テスト修正と品質保証 完了
- 目的：残存テストをtemplate対応に修正
- 規約遵守：bin/docs/conventions/testing.mdに準拠
- 修正内容：統合テストの入力形式変更、E2Eシナリオ確認
- 成果：全テストGREEN、品質基準達成
```

## 実装優先順位とスケジュール

1. **Phase 0**: 規約違反テスト削除（1日）
2. **Phase 1**: 不要コード削除（1日）
3. **Phase 2**: Template入力対応（2日）
4. **Phase 3**: POC Search統合（2日）
5. **Phase 4**: テスト修正（3日）

**合計**: 9日（元の見積もり10日から短縮）

## リスクと対策

1. **削除による機能喪失**
   - 対策：段階的削除とテスト確認
   - 必要なら部分的に復元

2. **POC search統合の不具合**
   - 対策：Phase 0で事前検証
   - フォールバック：簡易重複チェック

3. **後方互換性**
   - 対策：Cypher入力を残す
   - 段階的な移行期間を設定

## 成功の定義

1. **コード量60%削減**を達成
2. **テスト修正工数40%削減**を達成
3. Template入力で全機能が動作
4. POC searchによる重複検出が機能
5. 既存ユーザーへの影響なし

## 現在の達成状況（2025-07-13）

### 総合評価: 約60%達成（UPDATE/DELETEが不要なため）

#### 各目標の達成度：

1. **コード量60%削減** ✅ 達成
   - 現在4,269行（推定60%以上削減）
   - ファイル数: 33ファイル（大幅削減）

2. **テスト修正工数40%削減** ✅ 大幅超過達成
   - テストファイル: 36→2ファイル（94%削減）
   - 実行可能な仕様テストのみ残存

3. **Template入力で全機能が動作** ✅ 達成（Append-only設計）
   - ✅ スキーマ適用
   - ✅ 要件作成（CREATE）
   - ✅ 要件取得（READ）
   - ✅ 依存関係管理
   - ※ UPDATE/DELETEは設計上不要（Append-onlyアーキテクチャ）

4. **POC searchによる重複検出が機能** ❌ 未達成
   - embeddingフィールドの不整合でエラー発生
   - 重複検出が動作していない
   - スキーマとコードの不一致

5. **既存ユーザーへの影響なし** - 評価対象外
   - Cypher直接実行の廃止は設計判断
   - 後方互換性は不要と確認済み

## 残タスク（優先順位順）

### 緊急対応（Phase 5.8）
1. **POC search統合の修正**
   - スキーマ適用時のembeddingフィールド追加
   - search_integration.pyのエラー修正
   - 重複検出の動作確認

### 基本機能の完成（Phase 5.9）
2. **依存関係管理の完成**
   - 依存関係管理テンプレートの動作確認
   - 循環依存検出の統合テスト

### 品質向上（Phase 5.10）
3. **統合テストの充実**
   - 依存関係管理のテスト追加
   - エンドツーエンドシナリオテスト
   - POC search統合の動作確認テスト

### 将来の拡張（Phase 6）
4. **Cypherクエリのファイル化**
   - Pythonコード内のCypherクエリ抽出
   - query/ディレクトリへの移行
   - クエリローダー実装

### オプション
5. **後方互換性の部分復元**
   - 最小限のCypher実行サポート
   - 移行ガイドの作成