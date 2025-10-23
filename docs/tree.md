# Repository Tree (Latest Design Only)
> ADR本文にツリーは書かない。本ファイルのみ最新設計を更新。
> 5原則（SRP/KISS/YAGNI/SOLID/DRY）を徹底。必要になるまで実装しない（YAGNI）。

---

## 実装順（フェーズと最小到達点）

### P0（必須・最小で動く状態）
1. **SSOTを先に作る**（最小1エントリ）
   - `contracts/ssot/_toc.yaml`（id↔パス索引；仮でOK）
   - `contracts/ssot/_config.cue`（基本設定）
   - 例：`contracts/ssot/ugc/post@1.2.0/contract.cue`（schema最小＋stories≥3）
2. **index生成**
   - `tools/generator`：SSOT → `capsules/index.cue`（決定的生成）
   - `.gitignore`：`capsules/index.cue` を除外
   - Gate：**直import禁止**（indexのみ参照）
3. **薄いmanifest**
   - `features/**/manifest.cue`：`contractRef` のみ
   - `deployables/**/manifest.cue`：`import "capsules/index"` + `uses[]`
   - Gate：**存在チェック**（`uses[]` が index にあるか）
4. **gen 最小**
   - `tools/generator gen run/check`：`gen/tests|seeds|docs/**` 生成
   - **fingerprint一致**でCI Fail（手書き混入防止）
5. **CI直列**
   - `build(index) → cue vet → gen run → gen check → gates(min) → runner(min)`
   - runner最小：`pytest -m "smoke or unit"` / `go test`
6. **ポリシー最小**
   - `.pre-commit-config.yaml`：`cue fmt` / 直import禁止
   - `CODEOWNERS`：大束で開始（後で細分化）

### P1（堅牢化）
7. **determinism**
   - `jq -S`/`yq`でキー順固定・時刻/TZ/乱数除去
   - Gate：決定性チェック
8. **plan-diff強化 / changed-only**
   - 依存DAG差分（孤児/未提供/循環）→ Fail
   - 変更パスだけ実行（paths-filter）
9. **PII / golden-ttl**
   - `tools/mask`（PII検出・マスク）
   - ゴールデンの期限チェック

### P2（外部公開・スケール）
10. **dist（需要が出たら）**
    - `dist/contracts/{openapi,asyncapi,schema}/...` を**CIアーティファクトのみ**出力
    - Gate：`parity(index↔dist)`（逆投影/同値）
11. **シャーディング（閾値超えたら）**
    - index が重くなったら A–M/N–Z 分割→上位で合成
12. **ドキュ整備（必要になったら）**
    - Redoc/Pages公開、`contracts/reports/**` 可視化

---

## PoC/実験（下書き不要運用）
- `sandbox/**`（または `_poc/**`）配下に自由に作成可。**manifestが無い限り**スキャン対象外。
- **依存禁止**：indexに無いIDへの `uses[]` はFail。
- **TTLレポート**：長期放置は警告。昇格は「薄いmanifest追加 → SSOT登録 → index反映」。

---

## 最新ツリー（役割コメント＋フェーズ）

```
repo/
├─ contracts/                                   # 契約ドメインの集約 [P0]
│  └─ ssot/                                     # ★契約本文（人が編集）[P0]
│     ├─ _toc.yaml                              # id↔パス索引 [P0]
│     ├─ _config.cue                            # 生成/ゲートの設定 [P0]
│     ├─ ugc/
│     │  └─ post@1.2.0/{contract.cue,stories/**,seeds/**}   # 最小1件から [P0]
│     ├─ seo/...
│     └─ media/...
├─ capsules/                                    # ★内部インデックス（生成・非コミット）[P0]
│  └─ index.cue                                 # import先（唯一の参照点）[P0]
├─ features/                                    # 提供側（薄いmanifestのみ）[P0]
│  ├─ ugc/post/
│  │  ├─ manifest.cue                           # { contractRef }（schemaはSSOT）[P0]
│  │  └─ gen/{tests,seeds,docs}/**              # 生成物（fingerprint一致）[P0]
│  └─ ...
├─ deployables/                                 # 依存側（薄いmanifest）[P0]
│  ├─ api/public/
│  │  ├─ manifest.cue                           # import "capsules/index" + uses[] [P0]
│  │  └─ gen/{tests,seeds,docs}/**              # 生成物（fingerprint一致）[P0]
│  └─ ...
├─ sandbox/                                     # ★PoC/実験（manifestが無い限り完全除外）[随時]
│  └─ feature-x/…
├─ tools/                                       # 実行物の集約 [P0→P1]
│  ├─ generator/**                              # SSOT→index/gen/(opt:dist) [P0]
│  ├─ gates/**                                  # 直import/存在→determinism/plan-diff/PII [P0→P1]
│  ├─ runners/{python,go}/**                    # pytest/go test ラッパ [P0]
│  └─ mask/**                                   # PIIマスク/正規化 [P1]
├─ policy/                                      # 規約（宣言）[P1]
│  └─ cue/
│     ├─ vocab/{caps,errors,ratelimit}.cue      # 語彙 [P1]
│     └─ rules/{strict,determinism,contract-diff,...}.cue    # ルール [P1]
├─ dist/                                        # 外部配布（原則アーティファクト）[P2]
│  └─ contracts/{openapi,asyncapi,schema}/**
├─ ci/                                          # CI周辺 [P0→P1]
│  ├─ config/{phases.yaml,pipeline.yaml}        # 実行順/Fail条件 [P0]
│  ├─ reports/**                                # gates出力（diff/parity 等）[P1→P2]
│  └─ artifacts/**                              # 中間成果物 [P0]
├─ env/                                         # 環境テンプレ [P1]
│  └─ templates/{dev,stg,prod}.env
├─ .github/workflows/{ci.yml,nightly.yml,quarantine.yml}      # 直列パイプライン [P0]
├─ CODEOWNERS                                   # 大束で開始→細分化 [P0→P1]
├─ .pre-commit-config.yaml                      # cue fmt / 直import禁止 / secrets [P0]
├─ .gitignore                                   # capsules/index.cue, gen/** を除外 [P0]
└─ docs/
   ├─ adr/adr-0.10.8.md                         # 本ADR（final表記なし）[P0]
   └─ tree.md                                   # ←このファイル [P0]
```

---

必要なら、PoC TTLレポート用の最小スクリプト雛形と、paths-filter を使った changed-only CI例もすぐ出します。
