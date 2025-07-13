# Smart Threshold & Graph-Aware Duplicate Detection

## 概要

現在のembedding-onlyの重複検出を、グラフ構造を活用したより賢いアルゴリズムに改良する将来機能です。

## 現在の限界

### Embedding-onlyの問題点

**1. 文脈無視**
```json
// 現在: 文章類似度のみ
"JWT認証実装" vs "JWT認証システム" = 0.99類似度
// しかし依存関係・位置が全く違う可能性
```

**2. False Positive（偽陽性）**
```json
// 偶然似た文言だが異なる機能
A: "ユーザー登録機能" (フロントエンド要件)
B: "ユーザー登録機能" (データベース要件)
// embedding = 高類似度だが実際は別物
```

**3. 性能問題**
- 全要件に対してembedding計算
- 重複検出が重い処理として実行時間を延ばす

## 改良提案: 3段階ステート + グラフ構造活用

### 1. 拡張ステート管理

```sql
-- 現在
status ENUM('active', 'deleted')

-- 改良後
status ENUM('active', 'merge_candidate', 'deleted')
```

**段階的フロー:**
```json
{
  "active": "通常の要件（表示・検索対象）",
  "merge_candidate": "高類似度で統合待ち（要確認）", 
  "deleted": "統合完了・論理削除（非表示）"
}
```

### 2. 環境変数による段階的制御

```bash
# 閾値設定
SIMILARITY_BLOCK=0.95        # この値以上は即座拒否
SIMILARITY_CANDIDATE=0.85    # この値以上は統合候補
SIMILARITY_AUTO_MERGE=0.98   # 夜間自動統合対象
SIMILARITY_WARN=0.75         # 警告表示のみ

# 処理制御
BATCH_PROCESSING=true        # バッチ処理有効化
GRAPH_SIMILARITY=true        # グラフ構造考慮
DUPLICATE_CHECK_SCOPE=active # 検索対象（active/all）
```

**動作パターン:**
- `≥0.95`: 🚫 **即座拒否** + エラーレスポンス
- `0.85-0.94`: ⚠️ **統合候補** + `merge_candidate`状態で作成
- `0.75-0.84`: ⚠️ **警告表示** + 通常作成
- `<0.75`: ✅ **通常作成**

### 3. リアルタイム + バッチ分離

#### リアルタイム処理（軽量・高速）
```python
def create_requirement():
    # activeな要件のみを対象とした軽量チェック
    candidates = get_requirements(status='active')
    similarity = calculate_weighted_similarity(req, candidates)
    
    if similarity > BLOCK_THRESHOLD:
        return error("要件が重複しています", duplicates=candidates)
    elif similarity > CANDIDATE_THRESHOLD:
        status = "merge_candidate"  # 即座作成だが要確認
    else:
        status = "active"
    
    return create_with_status(req, status)
```

#### バッチ処理（重い処理・夜間実行）
```python
def nightly_merge_analysis():
    """夜間バッチ処理でより精密な重複検出・自動統合"""
    candidates = get_requirements(status='merge_candidate')
    
    # 高精度分析
    for req in candidates:
        similarity = deep_graph_analysis(req)
        
        if similarity > AUTO_MERGE_THRESHOLD:
            auto_merge_requirements(req)  # 自動統合
        elif similarity < CANDIDATE_THRESHOLD:
            req.status = 'active'  # 候補解除
    
    # 統合提案生成
    suggestions = generate_merge_suggestions(candidates)
    store_merge_suggestions(suggestions)
```

### 4. グラフ構造を活用した重複検出

#### Weighted Similarity Algorithm
```python
def weighted_similarity(req_a, req_b):
    """グラフ構造を考慮した重複度計算"""
    
    # 1. テキスト類似度（従来）
    embedding_sim = cosine_similarity(
        req_a.embedding, 
        req_b.embedding
    )
    
    # 2. 依存関係類似度
    dependency_sim = calculate_dependency_similarity(req_a, req_b)
    
    # 3. 階層位置類似度
    hierarchy_sim = calculate_hierarchy_similarity(req_a, req_b)
    
    # 4. グラフ距離
    graph_distance = calculate_graph_distance(req_a, req_b)
    
    # 重み付き総合スコア
    return (
        embedding_sim * 0.7 +      # テキスト内容
        dependency_sim * 0.2 +     # 依存関係
        hierarchy_sim * 0.1 -      # 階層位置
        graph_distance * 0.05      # グラフ距離（減点）
    )
```

#### 依存関係類似度
```python
def calculate_dependency_similarity(req_a, req_b):
    """依存関係のオーバーラップを計算"""
    
    # 共通の親要件
    common_parents = set(req_a.parents) & set(req_b.parents)
    total_parents = set(req_a.parents) | set(req_b.parents)
    parent_overlap = len(common_parents) / max(len(total_parents), 1)
    
    # 共通の子要件
    common_children = set(req_a.children) & set(req_b.children)
    total_children = set(req_a.children) | set(req_b.children)
    child_overlap = len(common_children) / max(len(total_children), 1)
    
    return (parent_overlap + child_overlap) / 2
```

#### 階層位置類似度
```python
def calculate_hierarchy_similarity(req_a, req_b):
    """階層構造における位置の類似性"""
    
    # 同じ階層レベル
    level_similarity = 1.0 if req_a.level == req_b.level else 0.0
    
    # 共通の祖先要件
    ancestors_a = get_all_ancestors(req_a)
    ancestors_b = get_all_ancestors(req_b)
    ancestor_overlap = len(ancestors_a & ancestors_b) / max(len(ancestors_a | ancestors_b), 1)
    
    return (level_similarity + ancestor_overlap) / 2
```

#### グラフ距離
```python
def calculate_graph_distance(req_a, req_b):
    """グラフ上の最短距離を計算"""
    try:
        distance = shortest_path_length(req_a, req_b)
        # 距離が近いほど類似度は高い（逆数）
        return 1.0 / (distance + 1)
    except NetworkXNoPath:
        # 連結していない場合は距離0
        return 0.0
```

## 具体的な改善例

### Case 1: 真の重複を正確に検出
```python
# Before: embedding-only
req_a = "JWT認証実装"
req_b = "JWT認証システム" 
similarity = 0.99  # 高類似度だが文脈不明

# After: graph-aware
req_a = {
    "title": "JWT認証実装",
    "dependencies": ["認証基盤"],
    "children": ["ログイン", "トークン更新"],
    "level": 3
}
req_b = {
    "title": "JWT認証システム",
    "dependencies": ["認証基盤"],  # 同じ親
    "children": ["ログイン", "トークン更新"],  # 同じ子
    "level": 3  # 同じレベル
}

weighted_similarity = 0.99 * 0.7 + 1.0 * 0.2 + 1.0 * 0.1 = 0.993
# → 真の重複として正しく検出
```

### Case 2: False Positiveを回避
```python
# Before: embedding-only
req_a = "ユーザー管理"
req_b = "ユーザー管理"
similarity = 1.0  # 完全一致だが...

# After: graph-aware
req_a = {
    "title": "ユーザー管理",
    "dependencies": ["DB設計"],
    "children": ["CRUD操作"],
    "level": 2
}
req_b = {
    "title": "ユーザー管理", 
    "dependencies": ["UI設計"],  # 異なる親
    "children": ["画面遷移"],   # 異なる子
    "level": 3  # 異なるレベル
}

weighted_similarity = 1.0 * 0.7 + 0.0 * 0.2 + 0.0 * 0.1 = 0.70
# → 同名の別要件として正しく判別
```

### Case 3: 関連要件の発見
```python
req_a = {
    "title": "決済システム",
    "dependencies": ["セキュリティ", "API基盤"],
    "children": ["クレジット決済", "銀行振込"]
}
req_b = {
    "title": "課金機能",
    "dependencies": ["セキュリティ", "API基盤"],  # 共通依存
    "children": ["月額課金", "従量課金"]
}

# 依存関係の類似性が高い → 統合候補として提案
dependency_similarity = 1.0  # 完全に共通の依存関係
# → "決済関連機能として統合を検討してください"
```

## データベーススキーマ拡張

### 要件エンティティ拡張
```sql
-- 新規カラム追加
ALTER TABLE RequirementEntity ADD COLUMN status ENUM('active', 'merge_candidate', 'deleted');
ALTER TABLE RequirementEntity ADD COLUMN hierarchy_level INT;
ALTER TABLE RequirementEntity ADD COLUMN graph_metrics JSON;

-- インデックス追加（性能最適化）
CREATE INDEX idx_requirement_status ON RequirementEntity(status);
CREATE INDEX idx_requirement_level ON RequirementEntity(hierarchy_level);
```

### マージ履歴テーブル
```sql
CREATE TABLE MergeHistory (
    id VARCHAR PRIMARY KEY,
    source_req_id VARCHAR NOT NULL,
    target_req_id VARCHAR NOT NULL,
    merge_type ENUM('auto', 'manual', 'suggested'),
    similarity_score FLOAT,
    merge_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_req_id) REFERENCES RequirementEntity(id),
    FOREIGN KEY (target_req_id) REFERENCES RequirementEntity(id)
);
```

### バッチ処理結果テーブル
```sql
CREATE TABLE BatchAnalysisResults (
    id VARCHAR PRIMARY KEY,
    analysis_date DATE,
    total_candidates INT,
    auto_merged INT,
    suggestions_generated INT,
    processing_time_ms INT,
    config_snapshot JSON
);
```

## API拡張

### 新規テンプレート

#### マージ実行
```json
{
  "type": "template",
  "template": "merge_requirements",
  "parameters": {
    "source_ids": ["req_002", "req_003"],
    "target_id": "req_001",
    "merge_strategy": "append",  // append/replace/manual
    "preserve_dependencies": true
  }
}
```

#### 統合候補確認
```json
{
  "type": "template", 
  "template": "list_merge_candidates",
  "parameters": {
    "min_similarity": 0.85,
    "limit": 20
  }
}
```

#### バッチ分析実行
```json
{
  "type": "template",
  "template": "run_batch_analysis", 
  "parameters": {
    "dry_run": true,  // 実際の変更は行わない
    "auto_merge_threshold": 0.98
  }
}
```

## 設定ファイル

### `config/smart_threshold.yaml`
```yaml
# Smart Threshold Configuration

similarity_thresholds:
  block: 0.95          # 作成拒否
  candidate: 0.85      # 統合候補
  auto_merge: 0.98     # 自動統合
  warning: 0.75        # 警告のみ

weights:
  embedding: 0.7       # テキスト類似度
  dependency: 0.2      # 依存関係類似度
  hierarchy: 0.1       # 階層位置類似度
  graph_distance: 0.05 # グラフ距離（減点）

batch_processing:
  enabled: true
  schedule: "0 2 * * *"  # 毎日2時に実行
  max_processing_time: "30m"
  
performance:
  embedding_cache_size: 10000
  graph_analysis_timeout: "5s"
  parallel_workers: 4

scope:
  duplicate_check: "active"  # active/all
  graph_analysis_depth: 5
```

## 実装計画

### Phase 1: 基盤整備
- [ ] データベーススキーマ拡張
- [ ] 環境変数による閾値制御
- [ ] ステート管理（active/merge_candidate/deleted）

### Phase 2: グラフ分析機能
- [ ] 依存関係類似度計算
- [ ] 階層位置類似度計算  
- [ ] グラフ距離計算
- [ ] 重み付き統合スコア

### Phase 3: バッチ処理
- [ ] 夜間自動分析ジョブ
- [ ] 自動統合機能
- [ ] 統合提案生成

### Phase 4: API拡張
- [ ] マージテンプレート
- [ ] 統合候補表示
- [ ] バッチ分析実行

### Phase 5: 最適化
- [ ] 性能チューニング
- [ ] キャッシュ機能
- [ ] 並列処理

## 期待される効果

### 精度向上
- **False Positive削減**: 同名でも異なる文脈の要件を正しく判別
- **True Positive向上**: 本当に重複している要件をより確実に検出
- **関連要件発見**: 統合すべき類似機能の提案

### 性能向上  
- **リアルタイム高速化**: activeな要件のみを対象とした軽量チェック
- **バッチ最適化**: 重い処理を夜間に分離
- **段階的処理**: 段階的な閾値による効率的なフィルタリング

### 運用性向上
- **自動化**: 明確な重複の自動統合
- **柔軟性**: 環境変数による閾値調整
- **透明性**: 統合履歴の完全追跡

## 互換性

### 既存機能との互換性
- 現在のembedding-based検出は維持
- 既存APIは変更なし（新規テンプレート追加のみ）
- データベースは後方互換性保持（新規カラム追加のみ）

### 段階的導入
1. **Phase 1**: 環境変数による閾値制御（即座に導入可能）
2. **Phase 2**: グラフ分析をオプション機能として追加
3. **Phase 3**: バッチ処理を段階的に有効化
4. **Phase 4**: 完全な自動化システム

この設計により、既存システムを壊すことなく段階的に高度な重複検出機能を導入できます。