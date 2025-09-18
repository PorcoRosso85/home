# CozoDB Time Travel機能テスト結果

## テスト概要

ここではCozoDBの時間的変化を追跡する機能（Time Travel）について、以下の2つの点を確認しました。

1. **異なるversion値を持つノードの最新値取得**: 複数のエンティティが異なる時点で更新された場合に、すべての最新値を正しく取得できるか
2. **バージョン値なしでのTime Travel**: バージョン値がない場合でもTime Travel機能を代替実装できるか

## テスト結果

### 1. Validityタイプでのテスト

CozoDBのドキュメント記述にある通り、`Validity`タイプを使用したリレーションでは`@ 'NOW'`構文や`@ '特定日付'`構文を使用したTime Travelが可能と記載されています。

**しかし、実際にテストしたところ、Node.js用のCozo-nodeライブラリの実装において以下の問題が確認されました**:

- `Validity`タイプを指定したリレーション作成自体は成功する
- しかし、データの挿入でエラーが発生する
- 明示的なエラーメッセージなしで実行が終了する

これはCozo-nodeライブラリの実装上の問題、または特定のバージョンでの不具合の可能性があります。Githubレポジトリの最終コミットは2023年12月で、対応が十分でない可能性があります。

### 2. 手動実装によるTime Travelの代替

問題の解決策として、`Validity`タイプを使わず、通常の文字列型として時間を保持し、手動でTime Travel機能を実装しました。

**その結果**:

1. **異なるversion値でのTime Travel**: 
   - 各ユーザーIDとタイムスタンプの組み合わせでデータを保存
   - 特定時点のデータを取得するクエリを自前で実装:
   ```
   latest_ts[uid, max(ts)] := *manual_status{uid, ts}, ts <= "${targetDate}"
   ?[uid, mood] := latest_ts[uid, ts], *manual_status{uid, ts, mood}
   ```
   - 現在（最新）のデータを取得するクエリを自前で実装:
   ```
   latest_ts[uid, max(ts)] := *manual_status{uid, ts}
   ?[uid, mood] := latest_ts[uid, ts], *manual_status{uid, ts, mood}
   ```

2. **異なるバージョン値でのテスト結果**:
   - 各エンティティが異なる時点で最終更新されていても、最新データのクエリは正しく動作
   - 例: Aliceは2024-02-01、Bobは2024-03-01、Charlieは2024-01-15が最新でも、すべて正しく取得できる

## 結論

1. Cozo-nodeライブラリ現バージョン（0.7.6）では`Validity`タイプを使用したTime Travel機能がうまく動作しない。

2. 代替手段として、通常の文字列型でタイムスタンプを保持し、自前でTime Travel機能を実装することは可能。

3. この代替手段により、**異なるバージョン値を持つエンティティの最新データを一度に取得**することが可能であることが確認できた。

## 推奨方法

現時点では、以下の方法でTime Travel機能を実装することをお勧めします：

1. 時間情報を通常の文字列型として保存
2. 以下のパターンのクエリで特定時点のデータを取得：
```
// 特定時点のデータ取得
latest_ts[uid, max(ts)] := *status_table{uid, ts}, ts <= "対象日付"
?[uid, value] := latest_ts[uid, ts], *status_table{uid, ts, value}

// 最新データの取得
latest_ts[uid, max(ts)] := *status_table{uid, ts}
?[uid, value] := latest_ts[uid, ts], *status_table{uid, ts, value}
```

これにより、異なるバージョン（時間）の最新値を一度に取得するというTime Travel機能の本来の目的を達成できます。
