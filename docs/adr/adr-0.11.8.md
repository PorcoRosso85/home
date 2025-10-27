# ADR 0.11.8: Manifest の責務定義（provides/consumes/redundant）と Capability ガバナンス方針
- **Status**: Proposed
- **Date**: 2025-10-25 (JST)
- **Relates**: ADR 0.11.4 / 0.11.5 / 0.11.6 / 0.11.7
- **Supersedes**: なし（0.11.4/0.11.6/0.11.7 を前提に**拡張**）

> **本PRは docs のみ**です。`docs/adr/adr-0.11.8.md` と `docs/tree.md` 以外を変更しません。
> 実装/CI/スキーマ/flake 変更は**後続PR**（実装系）で扱います。

---

## 0. 背景
- 0.11.4〜0.11.6 で、**Manifest は flake で CUE 生成（VCS 非追跡）**、**Guard の段階導入（warn/gate/fail）**、**CUE=SSOT** 等の原則を確立。
- 0.11.7 で DoD 整合を確認。
- 本ADRは「**Manifest に何を定義させるか（責務）**」を固定し、**能力（capability）重複のガバナンス方針**を文書化する（**docsのみ**）。

## 1. 決定（Docs方針）
1. **Manifest の必須/任意フィールド（責務）**
   - 最小（既存維持）:
     - `service: string`
     - `infra_deps: [...string]`
     - `forbidden?: [...string]`
   - 拡張（本ADRで方針確定／実装は後続PR）:
     - `provides: [...string]` … 本サービスが**提供**する capability-id
     - `consumes: [...string]` … 本サービスが**消費**する capability-id
     - `redundant?: { reason: "migration" | "canary" | "ha", ttlDays?: int }` … 一時的重複の**期限付き**許容

2. **Capability ガバナンスの共通語彙（docs定義）**
   - capability-id は **一意化**を目標に運用。
   - 排他性と適用範囲を**用語として**定義：
     - `exclusive: bool`（同一 scope で多重提供NG かの意図）
     - `scope: "repo" | "zone" | "env"`（排他判定のスコープ語彙）
   - ※ 本PRでは**概念だけ**定義。実データ/検査導入は後続PR。

3. **Guard 導入段階の再確認（docs）**
   - `guard_phase = warn | gate | fail` を**運用語彙**として採用。
   - 本PRは docs のみ（挙動変更なし）。

## 2. 目的
- `provides/consumes/redundant` を Manifest 責務として**明文化**し、
  **SRP 重複排除**の前提（意味の一意化・例外の期限管理）を**ドキュメントで確定**する。

## 3. スコープ / 非スコープ
- **スコープ（本PR）**: ドキュメント整備のみ
  - 本ADR（方針の明文化）
  - `docs/tree.md` への参照追記
- **非スコープ（後続PR）**: 実装/CI/スキーマ/flake の変更や追加

## 4. 期待効果（docs段階）
- 各サービスが「何を提供/消費するか」「一時重複の期限」を**宣言**する前提を整備。
- 以降の実装PRで、**重複検出の機械化**や**ゲート**を導入しやすくなる。

## 5. 影響
- **コード/CI/スキーマ/flake への影響はゼロ**（docsのみ）。
- 運用用語・責務の**読み物**としての基盤を提供。

## 6. 移行
- 本PR適用時点では**作業不要**。
- 後続PRで生成/検査系を段階導入する際に、各サービスで `provides/consumes/redundant` を順次追補。

## 7. 関連ADR
- 0.11.4（flake細粒度/manifest guard）
- 0.11.5（CUE=SSOT/leaf）
- 0.11.6（Secrets/Guard/IaC/Zoning確定）
- 0.11.7（DoD整合性確認）
