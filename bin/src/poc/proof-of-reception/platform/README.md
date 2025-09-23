# platform (共通基盤)

受領データへ共通ヘッダを付与し、冪等WALでR2へ耐久化し、来歴（監査証跡）を可搬に記録・出力する。

## コンポーネントと責務
- event-header（header付与）
  - 入: raw payload
  - 出: header付きevent（id/ts/kind/correlation）
  - しないこと: 業務判定・通知

- durable-log（冪等WAL→R2）
  - 入: header付きevent
  - 出: WAL offset + R2 URL（原本耐久化）
  - しないこと: 集計・検索

- audit-trail（監査バンドル出力）
  - 入: Correlation ID（event連結）
  - 出: audit bundle（manifest + 原本 + 主要メタ）
  - しないこと: ダッシュボード可視化

## ID/時刻・ハッシュ規約（推奨）
- evtId: UUIDv7
- corrId: W3C traceId（必要に応じてspanId）
- ts: ISO8601 UTC（Z）
- idempotencyKey: `src` + `contentHash`（SHA-256 of canonical payload）

## 契約（必須）
- `contracts/platform/event-header.json`（必須キー／相関要件）
- `contracts/platform/wal.json`（冪等キー・レコード形）
- `contracts/platform/audit-bundle.json`（証跡バンドルの構成）
- 互換方針: SemVerで後方互換優先（breakingは段階ロールアウト）

## SLO（初期）
- 受領→WAL書込 p99 < 1s、耐久化成功率 ≥ 99.99%
- 重複投入時の副作用ゼロ（idempotencyKeyで保証）
- 監査バンドルの完全性（Correlationで端〜端復元可能）

## ランブック（要旨）
- 健康チェック: 受領件数=WAL件数の乖離0／重複率／R2書込レイテンシ
- 障害時: Queue詰まり→バックプレッシャ調整／R2障害→ローカルWAL延長／再送はreplayへ委譲
- 不変条件（Invariants）: 同一idempotencyKeyは1回だけ反映＆audit bundleに欠損なし

## 将来の拡張（ここではやらない）
- ルール／通知／RBAC／PII／課金 → Phase2で `platform-*` を順次追加

