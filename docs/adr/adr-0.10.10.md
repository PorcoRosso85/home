# ADR 0.10.10 — Flake駆動マニフェスト / モジュール責務CUE / 厳格スキーマ / 決定的生成（中庸）

- **Status**: Accepted
- **Date**: 2025-10-23 (JST)
- **Owner**: Platform/Architecture
- **Scope**: contracts/ssot, features/**, deployables/**, tools/{bridge,generator,gates,runners,graph,paths-filter,mask}, policy/cue/**, .github/**

---

## 目的（要約）

- **宣言は Flake、仕様は SSOT、責務は CUE** に固定。
- **CIで flake→manifest.cue を決定的に生成**（非コミット）。
- **モジュールは 意図ヒント（intents） を薄く書き、部分集合パリティで整合を検証**。
- **生成物・検証を決定的にし、diff＝意図のみを実現**。

---

## 用語（固定）

- **feature**: 契約を「提供」する単位（1機能=1フレーク）。
- **deployable**: 起動/デプロイ単位（1プロセス=1フレーク）。
- **module**: 多言語実装の下位単位（manifestは増やさない）。
- **contract**: SSOTの契約（domain.subject@semver）。
- **uses/provides**: 依存/提供の意図。
- **story**: SSOTの受入シナリオ（正常/失敗/境界）。

---

## 決定（MUST/SHOULD）

### MUST

- **1機能=1フレーク、1デプロイ=1フレーク**。
- **flake2manifest による manifest.cue 自動生成**（非コミット）。
- **直 import 禁止**（参照は常に `import "capsules/index"`）。
- **全ルート/各モジュールに *.resp.cue 必須**（無ければCI Fail）— ※最終到達時（Phase C完了時）のMUST。段階移行はPhase A→B→C参照。
- **未知キー禁止**（CUEスキーマで強制）。

### SHOULD

- **intents.provides / intents.uses をモジュールに薄く記述**（中庸案）。
- **stability**（experimental/beta/ga/deprecated）と **visibility**（public/internal/private）を明示。
- **sandbox/** と resp.cue無し はスキャン除外（TTL警告あり）。

---

## スキーマ（抜粋・厳格）

```cue
// policy/cue/schemas/manifest.cue
Manifest: {
  kind:       "feature" | "deployable"
  owner:      string
  stability:  "experimental" | "beta" | "ga" | "deprecated"
  visibility: "public" | "internal" | "private"
  contractRef?: string      // kind=feature の時 必須
  uses?:       [...string]  // kind=deployable の時 必須
}

// policy/cue/schemas/module.cue
Module: {
  id:             string
  lang:           string
  role:           string
  allowedImports: ["capsules/index"] // 固定
  intents?: {
    provides?: [...string]
    uses?:     [...string]
  }
}
```

---

## パリティ & ゲート（要点）

### Parity（中庸）

- `⋃modules.intents.uses ⊆ flake.meta.manifest.uses`
- `⋃modules.intents.provides ⊆ {flake.contractRef 由来}`

### 整合/安全

- **plan-diff**: 孤児/未提供/循環
- **cap-dup**: 提供ID重複
- **contract-diff**: SemVer破壊
- **determinism**: 順序/時刻/TZ/乱数固定
- **mask/PII**: 個人情報検出
- **license/CVE**: ライセンス・脆弱性チェック

### 決定性

- `modules/*.resp.cue` をソート→ハッシュ→flake2manifest出力に埋め込み→ハッシュ不一致でFail。

### PoC TTL

- `sandbox/**` は N日（例:30）で警告→自動PR。

---

## CIフロー（短）

1. `nix build .#contracts-index` — SSOT→capsules/index.cue
2. `tools/bridge/flake2manifest` — flake→manifest.cue を .artifacts/ に決定的生成
3. `cue vet` — manifest と *.resp.cue をスキーマ検証
4. `tools/generator gen run/check` — gen/** 決定的生成＋指紋一致
5. `tools/gates/*` — parity/plan-diff/contract-diff/determinism/PII/license/CVE
6. `tools/runners/*` — タグで unit/smoke/integration…
7. `tools/graph` — 契約DAGをDOT/PNGで出力
8. `paths-filter` — changed-only 実行

---

## distポリシー / Backout / DX

### dist

- **リリースタグ時のみ固定化**（保持期限・再現手順を明記）。

### Backout

- **determinism / banned-tags を期限付きWARNへ段階緩和**。

### DX

- **devShells**（go/py/ts）
- **make ci-local**
- **PRテンプレ**（互換性/PII/SLOチェック欄）

---

## DoD（受入）

- ✅ ルート/モジュールの `*.resp.cue` あり＋cue vet 合格。
- ✅ flake2manifest 出力と modules-hash 一致。
- ✅ 直 import 0、plan-diff/cap-dup/contract-diff/determinism/PII/license OK。
- ✅ SSOT stories≥3、タグ実行ポリシー遵守。
- ✅ DAG/レポート生成済み（CIアーティファクト）。

---

## Relation to ADR 0.10.8

本ADR(0.10.10)は **0.10.8 の進化版**であり、最終的に置き換える。

- **一時併用**: 0.10.8の運用は P0期間のみ併用可（移行完了で廃止）。
- **互換**: 仕様の中心はSSOTで不変。運用面（flake/resp.cue/ゲート）を強化。

---

## Phased Rollout

### ゲート段階切替（一覧）

| ゲート/要件 | P0 | P1 | P2 |
|------------|----|----|-----|
| 直import禁止 | **Fail** | **Fail** | **Fail** |
| parity | Warn | **Fail** | **Fail** |
| resp.cue（ルート） | Warn | **Fail** | **Fail** |
| resp.cue（モジュール） | Warn | Warn | **Fail** |
| determinism | - | **Fail** | **Fail** |
| plan-diff / cap-dup | - | **Fail** | **Fail** |
| 未知キー禁止 | - | - | **Fail** |
| license / CVE | - | - | **Fail** |

### P0（最短・1–2週間）

- `flake2manifest` / parity/strict最小ゲート / SSOT→index→genの直列CI。
- 直import禁止を**Fail**、parity/resp.cueは**Warn**。
- **目安**: 1–2週間 / 1名。

### P1（堅牢化・2–3週間）

- `resp.cue`（ルート必須→モジュール推奨） / determinism / plan-diff / cap-dup。
- parityを**Fail化**、resp.cue（ルート）必須。
- **目安**: 2–3週間 / 1名。

### P2（拡張・2週間）

- license/CVEゲート / DAG可視化 / paths-filter（changed-only） / distポリシー。
- モジュールresp.cueを必須化、未知キー禁止。
- **目安**: 2週間 / 1名。

---

## *.resp.cue 移行戦略

### Phase A: 任意＋雛形生成

- 新規 feature/deployable に雛形自動生成。
- CIは**Warn**のみ。

### Phase B: ルート必須

- `features/deployables` ルートの resp.cue を必須化（**Fail**）。
- モジュールは**Warn**。

### Phase C: モジュール必須

- モジュールresp.cueも必須化、未知キー禁止、パリティ**Fail**。

### 救済措置

- `waiver.cue` に理由/期限/オーナーを記載（期限切れで自動Fail）。

---

## Tooling & Ownership

| ツール | サイズ | 工数 | 担当 |
|--------|--------|------|------|
| bridge/flake2manifest | S | 1–2日 | Platform |
| parity gate | S | 1日 | Platform |
| determinism gate | S | 1–2日 | Platform |
| plan-diff / cap-dup | M | 3–4日 | Platform |
| runners 最小 | XS | 0.5–1日 | 各言語担当 |
| graph(DAG) / paths-filter | S | 1–2日 | Platform |

**合計目安**: P0 ~1週・P1 ~2週・P2 ~2週（各1名）。小さく始めて拡張可。

---

## Numbering Note

- **ADR 0.10.9 はドラフト扱い**（未採択）。
- 混乱回避のため **0.10.10 を正式採番**。
- 必要に応じて 0.10.9 を「廃案」記録。

---

## 最小サンプル（抜粋）

### features/…/flake.nix

```nix
{
  outputs = { self, ... }: {
    meta.manifest = {
      kind = "feature";
      owner = "team-ugc";
      stability = "beta";
      visibility = "internal";
      contractRef = "ugc.post@1.2.0";
    };
  };
}
```

### deployables/…/flake.nix

```nix
{
  outputs = { self, ... }: {
    meta.manifest = {
      kind = "deployable";
      owner = "team-platform";
      stability = "ga";
      visibility = "public";
      uses = [ "ugc.post.create", "ugc.post.read" ];
    };
  };
}
```

### modules の例（module.resp.cue）

```cue
module: {
  id: "deployables.api.public.go-service"
  lang: "go"
  role: "service"
  allowedImports: ["capsules/index"]
  intents: { uses: ["ugc.post.create","ugc.post.read"] } // ⊆ flake.uses をゲート検証
}
```

---

## まとめ（改善点の効き目）

- ✅ **厳格スキーマ＋未知キー禁止**で書き方ブレを根絶。
- ✅ **中庸パリティ＋決定性ハッシュ**で flake↔module のズレを自動検出。
- ✅ **.artifacts 集約**で非コミット生成物を一元管理。
- ✅ **DAG可視化/changed-only**でレビューとCIをさらに高速化。

---

## 変更履歴

- 2025-10-23: 初版（Accepted）
