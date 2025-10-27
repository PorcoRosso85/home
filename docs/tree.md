# Repository Tree (Latest Design Only)

> ADR本文にツリーは書かない。本ファイルのみ最新設計を更新。
> 5原則（SRP/KISS/YAGNI/SOLID/DRY）を徹底。必要になるまで実装しない（YAGNI）。

**Last Updated**: 2025-10-27 (JST)
**対応ADR**: docs/adr/adr-0.11.3.md, docs/adr/adr-0.11.4.md, docs/adr/adr-0.11.5.md, docs/adr/adr-0.11.6.md, docs/adr/adr-0.11.7.md, docs/adr/adr-0.11.8.md, docs/adr/adr-0.1.0-spec-impl-mirror-flake-tag.md, docs/adr/adr-0.1.1-ci-runner-blacksmith.md, docs/adr/adr-0.1.2-tree-unify-and-guards.md
**運用原則**: この tree は宣言。未記載 = 削除。

---

## 最新ツリー（概観）

repo/
├─ flake.nix
├─ flake.lock
├─ README.md
├─ specification/                 # 0.1.2: Entrypointsを本体に統合
│  ├─ apps/[<scope>/]<name>/      # 直下に flake.nix を持つ entrypath（規約は ADR 0.1.0/0.1.2）
│  ├─ contracts/<name>/
│  ├─ infra/<name>/
│  ├─ interfaces/<name>/
│  └─ domains/<name>/
├─ contracts/                     # SSOT（実装禁止）
├─ infra/
│  ├─ flake.nix
│  ├─ runtimes/
│  ├─ adapters/
│  ├─ presentation-runtime/
│  ├─ content-build-tools/
│  └─ provisioning/               # OpenTofu（0.11.3）
│     ├─ modules/ environments/ state/ outputs/
│     ├─ cue/{schemas,checks}.cue
│     └─ scripts/{plan.sh,apply.sh,verify.sh,export-env.sh}
├─ domains/
├─ apps/
├─ interfaces/
├─ policy/
│  └─ cue/
│     ├─ schemas/{deps.cue,naming.cue,layout.cue}
│     └─ rules/{strict.cue,no-deps-outside-infra.cue,forbidden-imports.cue,outputs-naming.cue}
├─ ci/
│  └─ workflows/
│     ├─ apps-video.yml, http-video.yml, grpc-search.yml, web-search.yml
│     ├─ docs-build.yml, slides-export.yml, infra-deploy.yml
│     └─ ci-guard.yml             # 0.1.2: 最小ガード（lock/check/path:禁止/entry存在）※詳細は0.1.3
├─ scripts/
│  └─ validate-entrypaths.sh      # 0.1.2: 雛形（中身は0.1.3で強化）
└─ docs/
   ├─ adr/
   │  ├─ adr-0.11.3.md … adr-0.11.8.md
   │  ├─ adr-0.1.0-spec-impl-mirror-flake-tag.md
   │  ├─ adr-0.1.1-ci-runner-blacksmith.md
   │  └─ adr-0.1.2-tree-unify-and-guards.md
   ├─ tree.md (このファイル)
   ├─ architecture/{context.mmd,sequence.mmd}
   ├─ slides/example.md
   └─ dist/                        # 生成物（.gitignore）

---

## 運用方針（骨子）
- **specification/** は参照入口の**唯一の置き場**。`<entrypath>=<layer>/[<scope>/]<name>`、直下に `flake.nix`。
- **partial ブランチ**：`partial/<entrypath('/'→'-')>` を原則。PRは**小さく**、同一 entrypath は並行 1 本。
- **CI最小ガード（ci-guard）**：`nix flake lock --check` / `nix flake check`、`inputs.*.url` の `path:` 禁止、entrypath の存在確認。
- **自動統合**：`main` は branch protection。**ci-guard 緑**を required checks とし、条件を満たす PR は自動マージ可。
- **実行基盤**：GitHub Actions の runner は **Blacksmith** を標準（ADR 0.1.1）。例外はPR本文で理由/期限/代替を明記。

> 0.1.3 で強化する内容：SLO/コスト数値、entrypath 正規表現・重複検出、失敗メッセ定型、タグ掃除ルール 等。

---

## 4層構造（不変）
interfaces → apps → domains → contracts → infra

---

## 更新履歴
- 2025-10-27: ADR 0.1.2 適用（`specification/` を本体に統合、partial+CI最小ガードを明文化）
- 2025-10-25: ADR 0.1.0 適用、spec/impl mirror + Flakes参照 + 日付タグ
- 2025-10-25: ADR 0.1.1 適用、CI実行基盤: Blacksmith（docsのみ）
…（略）
