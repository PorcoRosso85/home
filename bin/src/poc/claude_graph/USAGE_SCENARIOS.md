# Claude Graph POC - 使用シナリオ

## 概要
ClaudeがKuzuDBグラフを活用して自律的にタスクを探索・計画するシナリオ集です。

## シナリオ1: 新機能実装の計画

### 状況
ユーザーが「ユーザー認証機能を実装したい」と依頼

### Claudeの動作
1. **要件探索**
   ```typescript
   // "認証"キーワードで要件を検索
   const authRequirements = await searchByKeyword("認証");
   ```

2. **依存関係の確認**
   ```cypher
   MATCH (r:RequirementEntity {id: 'req_user_auth'})-[:DEPENDS_ON*]->(d)
   RETURN d
   ```

3. **実装計画の生成**
   - 依存要件の実装状況確認
   - 未実装の依存要件を先に実装
   - テスト作成タスクも含める

### 結果
```
タスク計画:
1. req_user_model の実装（依存要件）
2. req_user_model のテスト作成
3. req_session_management の実装（依存要件）
4. req_session_management のテスト作成
5. req_user_auth の実装
6. req_user_auth のテスト作成
推定時間: 480分（8時間）
```

## シナリオ2: テストカバレッジ向上

### 状況
「テストが不足している部分を教えて」という依頼

### Claudeの動作
1. **テスト不足の検出**
   ```typescript
   const untestedReqs = await findUntestedRequirements();
   ```

2. **優先度付け**
   - 高優先度要件を先に
   - 依存される要件を優先

3. **テスト計画の提案**

### 結果
```
テストが必要な要件:
- req_payment_processing (優先度: High) - 5つの要件が依存
- req_data_validation (優先度: High) - 3つの要件が依存
- req_error_handling (優先度: Medium)

推奨アクション:
1. req_payment_processing の単体テスト作成
2. 統合テストの追加
3. エッジケースのテスト
```

## シナリオ3: リファクタリング影響分析

### 状況
「UserServiceクラスをリファクタリングしたい」

### Claudeの動作
1. **影響範囲の特定**
   ```cypher
   MATCH (c:CodeEntity {name: 'UserService'})<-[:REFERENCES_CODE]-(other)
   RETURN other
   ```

2. **関連要件の確認**
   ```cypher
   MATCH (c:CodeEntity {name: 'UserService'})<-[:IS_IMPLEMENTED_BY]-(r)
   RETURN r
   ```

3. **リスク評価とタスク生成**

### 結果
```
影響分析:
- 影響を受けるコード: 12ファイル
- 関連要件: 5件
- 必要なテスト更新: 8件

タスク計画:
1. UserServiceの新インターフェース設計
2. 依存コードの更新（12タスク）
3. テストの更新（8タスク）
4. 統合テストの実行
リスクレベル: 中
```

## シナリオ4: 進捗レポート生成

### 状況
「現在のプロジェクト状況を教えて」

### Claudeの動作
1. **全体統計の収集**
   ```typescript
   const stats = await gatherProjectStatistics();
   ```

2. **未完了タスクの分析**

3. **次のマイルストーンの提案**

### 結果
```
プロジェクト進捗レポート:

実装状況:
- 総要件数: 45
- 実装済み: 28 (62.2%)
- テスト済み: 22 (48.9%)

現在進行中:
- req_user_dashboard (実装中)
- req_notification_system (テスト作成中)

ボトルネック:
- req_external_api_integration が3つの要件をブロック

推奨次ステップ:
1. req_external_api_integration の優先実装
2. 高優先度要件のテスト作成
3. 技術的負債の解消
```

## シナリオ5: 自動問題検出

### Claudeの自律的な動作
定期的にグラフを分析し、問題を発見：

1. **循環依存の検出**
   ```cypher
   MATCH (r:RequirementEntity)-[:DEPENDS_ON*]->(r)
   RETURN r
   ```

2. **実装順序の違反**
   ```cypher
   MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->()
   WHERE EXISTS {
     MATCH (r)-[:DEPENDS_ON]->(d)
     WHERE NOT EXISTS {(d)-[:IS_IMPLEMENTED_BY]->()}
   }
   RETURN r
   ```

3. **アラートの生成**

### 結果
```
⚠️ 問題を検出しました:

1. 循環依存:
   req_module_a → req_module_b → req_module_c → req_module_a

2. 実装順序違反:
   req_advanced_feature が実装済みですが、
   依存要件 req_basic_feature が未実装です

推奨対応:
- 依存関係の見直し
- req_basic_feature の即時実装
```

## 活用のポイント

1. **自然言語での指示**
   - Claudeは曖昧な指示も理解し、適切なグラフクエリに変換

2. **コンテキストの保持**
   - 過去の探索結果を記憶し、より賢い提案

3. **プロアクティブな提案**
   - 問題を事前に検出し、解決策を提示

4. **統合的な視点**
   - 要件・実装・テストを総合的に分析