# Priority Recalculation POC Summary

## 概要

KuzuDBでの優先順位再計算システムの実装比較。UDFベースとアプリケーション層での実装を検証。

## TDD開発プロセス

### 1. RED Phase
- `test_priority_recalculation.py`: UDF関数が存在しないことを確認するテスト
- 現実的なシナリオをカバー（最優先事項の競合、挿入後の再配分など）

### 2. GREEN Phase
#### アプローチ1: UDF実装（制限あり）
- `priority_recalculation_simple.py`: スカラーUDFのみ実装可能
- KuzuDBの型制限により複雑なロジックは困難

#### アプローチ2: アプリケーション層実装（推奨）
- `priority_manager.py`: Pythonクラスによる完全な実装
- トランザクション制御、複雑なビジネスロジックに対応

## 実装比較

### UDFアプローチの問題点
```python
# 理想（動作しない）
def redistribute_priorities(requirements: List[Dict]) -> List[Dict]:
    # KuzuDBはList[Dict]型をサポートしない

# 現実（回避策）
def calc_redistributed_priority(current: int, index: int, total: int) -> int:
    # スカラー関数のみ、複数クエリが必要
```

### アプリケーション層の利点
```python
class PriorityManager:
    def redistribute_priorities(self) -> List[Dict]:
        # トランザクション制御
        self.conn.execute("BEGIN TRANSACTION")
        try:
            # 複雑なビジネスロジック実装可能
            # ...
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
```

## 現実的なシナリオ

### 1. 最優先事項の競合
```python
def test_multiple_urgent_priorities_competing():
    # 「これが最重要！」が複数発生
    # 現実: ステークホルダー全員が自分のタスクを最優先と主張
```

### 2. 優先順位のエスカレーション
```python
def test_priority_escalation_scenario():
    # 高優先度帯（240-255）が混雑
    # 新タスクを挿入するスペースが必要
```

### 3. バッチ挿入での衝突
```python
def test_batch_insert_with_redistribution():
    # 複数タスクの同時追加
    # 一意性を保証しながら原子的に処理
```

## 結論

### 推奨アーキテクチャ
1. **単純な計算**: UDF使用可（圧縮率計算など）
2. **複雑なビジネスロジック**: アプリケーション層
3. **一意性保証**: トランザクション + アプリケーション層

### UDFが適さない理由
- KuzuDBの型システム制限
- デバッグの困難さ
- ビジネスロジックの変更頻度
- テストの複雑さ

### アプリケーション層の優位性
- 完全なトランザクション制御
- 豊富な型システム
- 単体テストの容易さ
- ビジネスルールの明確な表現

## ファイル構成

```
priority_recalculation/
├── flake.nix                        # Nix開発環境
├── pyproject.toml                   # Python依存関係
├── README.md                        # プロジェクト説明
├── POC_SUMMARY.md                   # この文書
│
├── test_priority_recalculation.py   # TDD Red: UDF存在チェック
├── priority_recalculation_udf.py    # UDF実装（制限あり）
├── priority_recalculation_simple.py # 簡易UDF実装
├── test_priority_simple.py          # UDFテスト
│
├── priority_manager.py              # アプリケーション層実装
├── test_priority_manager.py         # TDD Green: 完全なテスト
└── demo_priority_recalculation.py   # デモンストレーション
```

## 学習事項

1. **KuzuDB UDFの制限**
   - 複雑な型（List[Dict]）は使用不可
   - ウィンドウ関数未対応
   - デバッグツール不足

2. **現実的な優先順位管理**
   - 最優先事項は常に変化する
   - 一意性保証は必須
   - バッチ処理での原子性が重要

3. **アーキテクチャ選択**
   - パフォーマンスvs保守性のトレードオフ
   - ビジネスロジックの配置は慎重に
   - テスタビリティを重視

## 次のステップ

1. パフォーマンステストの実施
2. 大規模データでの検証
3. リアルタイム優先順位調整の実装
4. 優先順位履歴管理の追加