# CozoDB Time Travel テスト結論

## テスト概要

CozoDBの時間的な変化を追跡する機能（Time Travel）について、以下の点を検証しました：

1. 異なるタイムスタンプ（バージョン）を持つエンティティの最新値を一度のクエリで取得できるか
2. バージョン値なしでもTime Travel機能を実装できるか

## テスト結果

### 実装方法の検証

CozoDBには2つの方法でTime Travel機能を実装できます：

1. **公式ドキュメントの方法（Validityタイプ）**
   - `Validity`タイプを使用してタイムスタンプを保存
   - `@ 'NOW'`や`@ '特定日付'`構文を使用してTime Travel
   - 現状のNode.js実装では正常に動作しない問題あり

2. **代替実装（手動Time Travel）**
   - 通常の文字列型としてタイムスタンプを保存
   - 各エンティティの特定日付以前の最新レコードを取得するクエリを自作
   - 完全に機能し、異なるバージョンのエンティティを一度に取得可能

### 1. 検証したこと

- 異なる時点でデータが更新された場合の最新データ取得
- 特定時点のデータ（過去のスナップショット）取得
- 複数のユーザーが異なるタイミングで最終更新された場合の挙動

### 2. 動作確認

動作確認したクエリパターン：

```
// 特定時点のデータ取得（Time Travel）
latest_ts[uid, max(ts)] := *status_table{uid, ts}, ts <= "対象日付" 
?[uid, value] := latest_ts[uid, ts], *status_table{uid, ts, value}

// 最新データ取得
latest_ts[uid, max(ts)] := *status_table{uid, ts}
?[uid, value] := latest_ts[uid, ts], *status_table{uid, ts, value}
```

このパターンにより、以下が実現できます：
- 特定時点の全エンティティの状態取得（過去のスナップショット）
- 全エンティティの最新状態取得（最終更新時刻が異なる場合も対応）

## 結論

1. Cozo-node（Node.js実装）では`Validity`タイプによるTime Travel機能が期待通り動作しない

2. 代替実装として、タイムスタンプを文字列型で保存し、手動でTime Travel機能を実装することで同等の機能を実現できる

3. 代替実装では、**異なるタイムスタンプ（バージョン）を持つエンティティの最新値を正しく取得できる**ことを確認

## 推奨実装パターン

現時点では、以下の実装パターンを推奨します：

1. データモデル：
```
:create entity_history {
  entity_id: String,
  timestamp: String =>
  data: String  // または必要な型
}
```

2. 特定時点のスナップショット取得：
```
latest_ts[entity_id, max(timestamp)] := *entity_history{entity_id, timestamp}, timestamp <= "対象日付" 
?[entity_id, data] := latest_ts[entity_id, timestamp], *entity_history{entity_id, timestamp, data}
```

3. 最新データの取得：
```
latest_ts[entity_id, max(timestamp)] := *entity_history{entity_id, timestamp}
?[entity_id, data] := latest_ts[entity_id, timestamp], *entity_history{entity_id, timestamp, data}
```

この実装パターンにより、CozoDBのTime Travel機能の本質的な要件である「異なるタイムスタンプを持つエンティティの最新値取得」が実現できます。
