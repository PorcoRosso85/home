# 矛盾検出機能仕様書

## 概要

requirement/graphシステムの主要目的の一つである「矛盾の検出」機能の仕様を定義する。
現在は未実装のため、test_contradiction_detection.pyに将来の期待される動作を記述している。

## 矛盾タイプ

### 1. 相互排他（Mutual Exclusion）
- **定義**: 同時に存在できない要件
- **例**: "オンプレミス専用" vs "クラウド専用"
- **検出方法**: 要件の説明文から排他的キーワードを抽出し、矛盾を検出

### 2. 依存関係の矛盾（Dependency Conflict）
- **定義**: A requires B, C excludes B の関係で、AとCが両方必要な場合
- **例**: "高セキュリティモード" requires "ネットワーク遮断", "リアルタイム同期" excludes "ネットワーク遮断"
- **検出方法**: 依存グラフの推移的クロージャを計算し、矛盾パスを検出

### 3. 時間的矛盾（Temporal Conflict）
- **定義**: 時間的制約が競合する要件
- **例**: "24時間365日稼働" vs "日次メンテナンス必須"
- **検出方法**: 稼働率要求と停止時間要求を比較

### 4. リソース矛盾（Resource Conflict）
- **定義**: リソース制約が競合する要件
- **例**: "メモリ使用量100MB以下" vs "10GBデータのメモリ展開"
- **検出方法**: 要求リソースと利用可能リソースを比較

### 5. 論理的不整合（Logical Inconsistency）
- **定義**: 論理的に両立しない条件
- **例**: "全ユーザーアクセス可能" vs "特定ユーザーのみアクセス可能"
- **検出方法**: アクセス制御ポリシーの矛盾を検出

## API仕様

### check_contradictionsテンプレート

```json
{
  "type": "template",
  "template": "check_contradictions",
  "parameters": {
    "scope": "all",  // "all" or specific requirement IDs
    "include_suggestions": true
  }
}
```

### 期待される出力

```json
{
  "status": "success",
  "contradictions_found": 3,
  "contradictions": [
    {
      "id": "contradiction_001",
      "type": "mutual_exclusion",
      "severity": "high",
      "requirements": ["req_onprem_only", "req_cloud_only"],
      "description": "These requirements are mutually exclusive",
      "suggestion": "Consider creating separate system variants or removing one requirement"
    }
  ],
  "summary": {
    "by_type": {
      "mutual_exclusion": 1,
      "dependency_conflict": 1,
      "temporal_conflict": 1
    },
    "by_severity": {
      "high": 2,
      "medium": 1,
      "low": 0
    }
  }
}
```

## 実装ガイドライン

### 1. 検出エンジン
- 各矛盾タイプごとに専用の検出器を実装
- 並列実行可能な設計
- 増分検出対応（新規要件追加時の差分検出）

### 2. 重要度判定
- **High**: プロジェクト進行不可能な矛盾
- **Medium**: 修正が推奨される矛盾
- **Low**: 注意が必要な潜在的矛盾

### 3. 修正提案
- 各矛盾タイプに応じた具体的な修正案を提示
- 複数の選択肢がある場合はすべて提示

### 4. 統合ポイント
- create_requirement時の事前チェック
- add_dependency時の循環・矛盾チェック
- 定期的な全体スキャン

## テストカバレッジ

test_contradiction_detection.pyで以下をカバー：
- 各矛盾タイプの基本的な検出
- APIインターフェースの仕様
- 将来の実装時の期待される動作

## 関連ファイル

- `test_contradiction_detection.py`: 仕様テスト
- `README.md`: 将来対応として記載
- `TEST_PURPOSE_ALIGNMENT.md`: 主要目的として言及