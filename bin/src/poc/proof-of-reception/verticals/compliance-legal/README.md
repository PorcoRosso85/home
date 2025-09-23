# compliance-legal（法務コンプラ）

規制/開示イベントの監視→耐久→監査再現を“最短の価値線”で提供する垂直機能。

## コンポーネントと責務
- monitor（監視→封入→耐久）
  - 処理: ソース監視 → `platform/event-header` でheader付与 → `platform/durable-log` へ耐久
  - しないこと: 重要度判定・通知

- tracker（監査バンドル生成）
  - 処理: 入力→差分→判定→通知素材を `platform/audit-trail` 規約でバンドル化
  - しないこと: 恒久ストレージの設計変更

## 成果KPI
- 重要開示の検知→audit bundle生成までの中央値（rolling 7d）と p95
- 証跡欠落ゼロ（件数/割合）
- 監査要求への一次応答時間

## ビジネス理由（なぜ今）
- 罰金・差し戻し・訴訟コストに直結＝高単価でも決裁されやすい
- 既存大手の弱点（来歴の完全再現・版管理）を補完しやすい
- サーバレス骨格（Workers/Queues/R2）で低ランニング・早期PoC→本番化が容易

## 入出力契約（最低限）
- `contracts/compliance-legal/source.json`（監視対象の定義：例=官報/EDGAR/TDNet）
- `contracts/compliance-legal/diffset.json`（条項/文の差分セット形式）
- `contracts/compliance-legal/audit-brief.json`（監査向け要約の型）

## 運用上の約束（Definition of Done）
- monitor が冪等（重複入稿時の副作用ゼロ）
- tracker が同一Correlationで端〜端の証跡を束ねる
- audit bundle をワンクリックで再生成できる（再現性）

