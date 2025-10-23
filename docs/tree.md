# Repository Tree (Latest Design Only)
> ADR本文にツリーは書かない。本ファイルのみ最新設計を更新。
> 5原則（SRP/KISS/YAGNI/SOLID/DRY）を徹底。必要になるまで実装しない（YAGNI）。

---

## 実装順（フェーズと最小到達点）

### P0（必須・最小で動く状態・1–2週間）

1. **SSOTを先に作る**（最小1エントリ）
   - `contracts/ssot/_toc.yaml`（id↔パス索引；仮でOK）
   - `contracts/ssot/_config.cue`（基本設定）
   - 例：`contracts/ssot/ugc/post@1.2.0/contract.cue`（schema最小＋stories≥3）

2. **flake2manifest**
   - `tools/bridge/flake2manifest`：flake→manifest.cue を決定的生成
   - `.gitignore`：`capsules/index.cue`, `.artifacts/**` を除外
   - Gate：**直import禁止**（indexのみ参照）

3. **薄いmanifest（Flake駆動）**
   - `features/**/flake.nix`：`meta.manifest.kind="feature", contractRef, owner, stability`
   - `deployables/**/flake.nix`：`meta.manifest.kind="deployable", uses=[], owner`
   - Gate：**存在チェック**（`uses[]` が index にあるか）

4. **resp.cue（ルート）**
   - `features/**/meta/impl.resp.cue`：役割/可視性/allowedImports
   - `deployables/**/meta/service.resp.cue`：SLO/ポート
   - Phase A: **Warn**のみ

5. **gen 最小**
   - `tools/generator gen run/check`：`gen/tests|seeds|docs/**` 生成
   - **fingerprint一致**でCI Fail（手書き混入防止）

6. **CI直列**
   - `build(index) → flake2manifest → cue vet → gen run → gen check → gates(min) → runner(min)`
   - runner最小：`pytest -m "smoke or unit"` / `go test`

7. **ポリシー最小**
   - `.pre-commit-config.yaml`：`cue fmt` / 直import禁止 / secrets
   - `CODEOWNERS`：大束で開始（後で細分化）

### P1（堅牢化・2–3週間）

8. **resp.cue（ルート必須化）**
   - Phase B: ルートresp.cueを**Fail化**
   - モジュールresp.cueは**Warn**

9. **determinism**
   - `jq -S`/`yq`でキー順固定・時刻/TZ/乱数除去
   - Gate：決定性チェック

10. **plan-diff / cap-dup**
    - 依存DAG差分（孤児/未提供/循環）→ Fail
    - capability重複検出→ Fail

11. **parity強化**
    - `⋃modules.intents ⊆ flake.manifest`
    - Phase B: **Fail化**

12. **PII / golden-ttl**
    - `tools/mask`（PII検出・マスク）
    - ゴールデンの期限チェック

### P2（拡張・2週間）

13. **resp.cue（モジュール必須化）**
    - Phase C: モジュールresp.cueも**Fail化**
    - 未知キー禁止

14. **license / CVE**
    - ライセンスチェック
    - CVE突合

15. **dist（需要が出たら）**
    - `dist/contracts/{openapi,asyncapi,schema}/...` を**CIアーティファクトのみ**出力
    - Gate：`parity(index↔dist)`（逆投影/同値）

16. **graph / paths-filter**
    - 契約DAG可視化
    - 変更パスだけ実行（changed-only）

17. **シャーディング（閾値超えたら）**
    - index が重くなったら A–M/N–Z 分割→上位で合成

18. **ドキュ整備（必要になったら）**
    - Redoc/Pages公開、`contracts/reports/**` 可視化

---

## PoC/実験（下書き不要運用）

- `sandbox/**`（または `_poc/**`）配下に自由に作成可。**manifestが無い限り**スキャン対象外。
- **依存禁止**：indexに無いIDへの `uses[]` はFail。
- **TTLレポート**：長期放置は警告。昇格は「薄いmanifest追加 → SSOT登録 → index反映」。

---

## 最新ツリー（ADR 0.10.10 — Flake駆動マニフェスト）

> 凡例: ★=必須、◇=生成(非コミット推奨)、△=任意

```
repo/
├─ flake.nix                               △  ルート開発環境/DevShell等（任意）
├─ flake.lock                              △
├─ .gitignore                              ★  capsules/index.cue, gen/**, .artifacts/** を除外
├─ .editorconfig                           △
├─ .pre-commit-config.yaml                 △  cue fmt / secrets 等
├─ Makefile                                △  `make ci-local` など
├─ CODEOWNERS                              △
├─ README.md                               △
├─ docs/
│  ├─ adr/
│  │  ├─ adr-0.10.8.md                     △  既存
│  │  └─ adr-0.10.10.md                    ★  改善版ADR
│  └─ tree.md                              △  最新ツリー説明（本ファイル）
├─ contracts/
│  └─ ssot/                                ★  仕様本文（人が編集）
│     ├─ _toc.yaml                         ★  契約ID↔パス索引
│     ├─ _config.cue                       ★  生成/ゲート設定
│     ├─ ugc/
│     │  └─ post@1.2.0/
│     │     ├─ contract.cue                ★  schema/caps/errors/rateLimit 等
│     │     ├─ stories/                    ★  正常/失敗/境界 ≥3
│     │     │  ├─ normal.cue
│     │     │  ├─ error.cue
│     │     │  └─ boundary.cue
│     │     └─ seeds/                      △
│     │        └─ post.json
│     └─ ...（他ドメイン）
├─ features/
│  └─ <domain>/<feature>/                  ★  1機能=1フレーク
│     ├─ flake.nix                         ★  meta.manifest.kind="feature", contractRef, owner, stability...
│     ├─ meta/                             ★  （旧 cue.README/）
│     │  ├─ impl.resp.cue                  ★  役割/可視性/allowedImports=["capsules/index"]
│     │  └─ modules.resp.cue               △  modules 共通規約
│     ├─ modules/                          △  多言語実装（manifestは増やさない）
│     │  ├─ go-api/
│     │  │  ├─ go.mod / main.go / ...
│     │  │  └─ module.resp.cue             ★  intents.provides 等（薄く）
│     │  ├─ py-jobs/
│     │  │  ├─ pyproject.toml / jobs/**
│     │  │  └─ module.resp.cue             ★
│     │  └─ ts-sdk/
│     │     ├─ package.json / src/**
│     │     └─ module.resp.cue             ★
│     └─ gen/                              ◇  tests/seeds/docs（指紋一致）
│        ├─ tests/{unit,integration,e2e,uat}/**
│        ├─ seeds/**
│        └─ docs/**
├─ deployables/
│  └─ <tier>/<name>/                       ★  1デプロイ=1フレーク
│     ├─ flake.nix                         ★  meta.manifest.kind="deployable", uses=[...], owner...
│     ├─ meta/
│     │  ├─ service.resp.cue               ★  ポート/SLO/公開範囲
│     │  └─ deps.resp.cue                  ★  uses と parity 検証（flakeと部分集合一致）
│     ├─ modules/
│     │  ├─ go-service/
│     │  │  ├─ main.go / ...
│     │  │  └─ module.resp.cue             ★  intents.uses ⊆ flake.uses
│     │  ├─ py-migrations/
│     │  │  ├─ scripts/**
│     │  │  └─ module.resp.cue             ★
│     │  └─ ts-proxy/
│     │     ├─ src/**
│     │     └─ module.resp.cue             ★
│     └─ gen/                              ◇
│        ├─ tests/**
│        └─ docs/**
├─ capsules/                               ◇  生成（非コミット）
│  └─ index.cue
├─ .artifacts/                             ◇  非コミット生成物の集約
│  ├─ manifests/
│  │  ├─ features/<domain>/<feature>/manifest.cue
│  │  └─ deployables/<tier>/<name>/manifest.cue
│  └─ reports/
│     ├─ parity.json
│     ├─ plan-diff.json
│     ├─ contract-diff.json
│     ├─ determinism.json
│     ├─ license.csv
│     └─ dag.dot / dag.png
├─ tools/
│  ├─ bridge/
│  │  └─ flake2manifest                    ★  flake→manifest.cue（決定的・非コミット）
│  ├─ generator/
│  │  ├─ gen                               ★  SSOT→gen/dist
│  │  └─ check                             ★  指紋検証
│  ├─ gates/                               ★  失敗で止める
│  │  ├─ parity.cue                        # modules ⊆ flake（uses/provides）
│  │  ├─ plan-diff.cue                     # 孤児/未提供/循環
│  │  ├─ contract-diff.cue                 # SemVer破壊
│  │  ├─ cap-dup.cue                       # 提供ID重複
│  │  ├─ determinism.cue                   # 決定性
│  │  ├─ mask.cue                          # PII
│  │  ├─ license.cue                       # ライセンス
│  │  └─ cve.cue                           # CVE
│  ├─ runners/
│  │  ├─ python/runner.sh                  ★  タグ実行（unit/smoke等）
│  │  └─ go/runner.sh                      ★
│  ├─ graph/
│  │  └─ build-graph.sh                    △  契約DAG可視化
│  └─ paths-filter/
│     └─ filters.yml                       △  changed-only 実行
├─ policy/
│  └─ cue/
│     ├─ schemas/
│     │  ├─ manifest.cue                   ★  厳格スキーマ（未知キー禁止）
│     │  ├─ module.cue                     ★
│     │  └─ responsibility.cue             ★
│     └─ rules/
│        ├─ strict.cue                     ★  直import禁止 等
│        ├─ determinism.cue                ★
│        ├─ contract-diff.cue              ★
│        ├─ plan-diff.cue                  ★
│        ├─ cap-dup.cue                    ★
│        ├─ parity.cue                     ★
│        ├─ mask.cue                       ★
│        ├─ license.cue                    ★
│        └─ cve.cue                        ★
├─ dist/                                   △  リリース時のみ固定化
│  └─ contracts/{openapi,asyncapi,schema}/**
├─ sandbox/                                △  PoC（TTL警告・スキャン除外）
│  └─ feature-x/
└─ .github/
   ├─ workflows/
   │  ├─ ci.yml                            ★  直列: index→flake2manifest→vet→gen→gates→runners→graph→paths-filter
   │  ├─ nightly.yml                       △
   │  └─ quarantine.yml                    △
   ├─ PULL_REQUEST_TEMPLATE.md             △  互換性/PII/SLO チェック欄
   └─ ISSUE_TEMPLATE/{bug_report.md,feature_request.md}  △
```

---

## 使い方の要点（0.10.10版）

**人が編集**:
- `contracts/ssot/**`
- `features/**/flake.nix`
- `deployables/**/flake.nix`
- 各 `*.resp.cue`

**自動生成**:
- `capsules/index.cue`
- `.artifacts/manifests/**`
- `features|deployables/**/gen/**`

**検証**:
- CIの`gates/*`で parity / plan-diff / contract-diff / determinism / PII / license / CVE をFail化

---

## フェーズ実装チェックリスト（0.10.10版）

### P0で必須
- [ ] `bridge/flake2manifest`
- [ ] `gates/parity|strict`
- [ ] `capsules/index.cue` 生成
- [ ] `runners` 最小

### P1で必須
- [ ] `policy/cue/schemas/{manifest,module,responsibility}.cue`
- [ ] `gates/{determinism,plan-diff,cap-dup}`

### P2で必須
- [ ] `tools/{graph,paths-filter}`
- [ ] `gates/{license,cve}`
- [ ] `dist/` 方針
