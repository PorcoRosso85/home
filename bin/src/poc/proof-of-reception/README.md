# proof-of-reception

Reception → Preservation → Presentation を最短経路で実現する「骨格＋共通関節」を提供するリポジトリ。

## 目的
- すべての入力に Who/When/Correlation を与え、ゼロデータロスと監査再現性を保証する。
- サーバレス骨格（VPS/OTel, Queue, R2, Workers）＋軽量な出口（DuckDB meta-index）で、低コスト・高信頼の証跡基盤を成立させる。

## 範囲（Scope）
- 骨格: Ingress／Queue／WAL→R2／Runner／Index（DuckDB meta-indexはPhase1では“薄く”）
- 共通関節（最小セット）: `platform/event-header`／`platform/durable-log`／`platform/audit-trail`
- 初期垂直: `verticals/compliance-legal`（監視=monitor、証跡束=tracker）

## 非目的（Non-goals）
- 巨大RDB運用・重厚DWH/BI、配信名簿管理、請求書発行、IDプロバイダそのもの。
- ルールエンジン／通知ハブはPhase2で段階投入（本フェーズは価値線の成立に集中）。

## 設計原則
- SRP / KISS / YAGNI / SOLID / DRY
- Queueで疎結合、WALで冪等耐久、スキーマ互換を優先、来歴（audit bundle）の完全復元を最重要。

## 価値線（最短で届ける価値）
- 受付 → 耐久化（R2） → 監査再現（audit bundle出力） → 通知（通知ハブは後段追加）

## 成功KPI（計測可能なもののみ）
- 受領→WAL書込成功率 ≥ 99.99%
- 重複受領の冪等率 100%
- 監査再現率 100%（同一Correlation IDで端〜端を復元可能）
- 検知→エクスポートTTRの中央値（rolling 7d）と p95 の継続短縮

## ディレクトリ
- `platform/*`  共通関節（横断機能）
- `verticals/compliance-legal/*`  垂直（法務特化）
- `contracts/*`  入出力契約（JSON/Nickel）

## 運用・意思表示
- 単一責務: 1ディレクトリ=1機能。入出力は `contracts/*` で固定、実装は差し替え可能。
- 監査再現: Correlation IDで当時の入力・ルール・出力を束ね、audit bundleとしてエクスポート可能に。
- 漸進投入: まず法務の価値線に集中。RBAC/PII/課金はPhase2以降。

