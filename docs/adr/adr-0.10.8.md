# ADR 0.10.8 — タグ駆動SSOT / 薄いマニフェスト / 決定的生成 / PoC除外

- **Status**: Accepted
- **Date**: 2025-10-23 (JST)
- **Owner**: Platform/Architecture
- **Scope**: contracts/ssot, capsules/index, tools/{generator,gates,runners,mask}, CI, dist(任意), sandbox/**

## 結論（要点）
- **SSOT集中**：契約本文（schema/caps/errors/rateLimit/interfaces/stories/seeds）は **contracts/ssot/** のみ。
- **薄いマニフェスト**：各 `features|deployables/**/manifest.cue` は **contractRef と uses だけ**（参照＋依存）。**schema本文は書かない**。
- **参照統一**：依存側は **常に** `import "capsules/index"` を参照（**直import禁止**）。
- **決定的生成**：同一 `flake.lock` で `capsules/index.cue` と生成物は **バイト等価**（順序/TZ/乱数/時刻を固定）。
- **生成の一方向**：SSOT → index（内部） → gen（各dir）/ dist（外部）。逆流なし。
- **PoCは除外**：`sandbox/**`（または `_poc/**`）配下や**manifestが無いディレクトリ**は**スキャン対象外**（index/gen/dist/テストに影響なし）。
- **dist**：外部/別チーム/人向けの配布形（OpenAPI/AsyncAPI/Schema）。**原則コミットせず**、CIアーティファクト or リリース時のみ固定。

## テスト責務（SSOTで一元）
- **stories≥3**（正常/失敗/境界、`tags:[unit,integration,e2e,uat,smoke]`）。
- **非機能**：`p95_ms`, `error_rate` 等。
- **生成**：generator が各 `gen/tests|seeds|docs/**` を**決定的生成**（fingerprint一致で検証）。
- **実行**：pytest/go は置換せず **runners** からタグ選択実行。

## Quality Gates（Failの代表）
- `cases≥3` / `banned-tags`（降格不可）
- `contract-diff`（破壊変更/SemVer整合）
- `plan-diff`（Uses↔提供の孤児/未提供検出）
- `determinism`（順序/時刻/TZ/乱数/整形の固定）
- `parity(index↔dist)`（逆投影の同値確認）
- `mask/PII` / `golden-ttl`
- **直import禁止**：`features/**` 直参照はFail
- **PoC依存禁止**：indexに無いIDへの `uses[]` はFail

## PoC/実験（下書き不要運用）
- **OK**：ディレクトリだけ先に作ってもよい（manifest未作成のまま可）。
- **除外規則**：`sandbox/**` または `_poc/**`、**manifest不在**は**自動でスキャン除外**。
- **TTL**：`sandbox/**` の長期放置は**レポート**（警告）。昇格時は (1) 薄いmanifest追加 → (2) SSOT登録 → (3) index反映。

## CI（骨子・直列固定）
1. `nix build .#contracts-index` → **index生成（capsules/index.cue）**
2. `cue vet`（SSOT/薄いmanifestの整合）
3. `tools/generator gen run` → `gen check`（fingerprint一致）
4. `tools/gates/*`（直import/存在 → contract-diff/plan-diff/determinism/PII 等）
5. `tools/runners/*`（PR=unit+smoke / merge=integration / nightly=e2e / release=uat）
6. （必要時）`export-contracts` → `dist/contracts/**` 生成 → `parity`

## 優先度（P0→P1→P2）
- **P0**：index生成 / plan-diff・changed-only / fingerprint / runner / CI配線
- **P1**：determinism / PII・golden-ttl
- **P2**：dist出力（外部需要でP0へ格上げ可）/ シャーディング

## 命名・メタ（生成物共通）
- 形式：`<subject>--<kind>--<version>@<short-sha>.<ext>`
- メタ：`x-origin.manifest`, `x-origin.commit`, `x-build.time`

## Backout
- 一時的に `banned-tags`/`determinism` を WARNING 化。
- `gen check` スキップは期限付き（dist公開は継続）。

## 例（最小）
```cue
// SSOT: contracts/ssot/ugc/post@1.2.0/contract.cue
contract: { id: "ugc.post", version: "1.2.0", owner: "team-ugc" }
schema:  { req: {...}, res: {...}, _: _|_ }
stories: [ {id:"POST-101", tags:["integration","smoke"], ...}, ... ]

// 薄いmanifest: deployables/api/public/manifest.cue
import "capsules/index"
contractRef: "deployables.api.public"
uses: ["ugc.post.create","ugc.post.read"]

// PoC（除外例）
sandbox/feature-x/   # manifest.cue が無い限りスキャン対象外
```
