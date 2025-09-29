DELETE WHEN NO LONGER NEEDED (FACTS ONLY)

**目的（dir/flake）**
- ゼロCloudflareのpSEO基盤（flakeで開発/型検査/ビルド/検証を完結）。
- 構成要素: 計測スニペット（IIFE/ESM）、JSON‑LDジェネレータ、静的SEO生成（1.1で追加）。

**Phase 1.0 完成形（事実）**
- 計測スニペット: `packages/measurement/snippet.ts` → 出力 `dist/measurement/snippet.{esm,iife}.js`
- JSON‑LD: `packages/seo/{image-object.ts, collection.ts, howto.ts}`
- 例/検証: `examples/phase-1.0/*`, `docs/testing/phase-1.0.md`
- Flake apps: `check`, `build-snippet`, `serve-examples`
- 参照コミット（最終Fix）: `b3be2559` fix: complete Phase 1.0 programmatic SEO foundation fixes
  - （実装本体）`d9d4418d` feat: implement complete Programmatic SEO Phase 1.0 foundation

**Phase 1.1 完成形（事実）**
- 追加スクリプト: `scripts/build-sitemap.ts`, `scripts/build-hreflang.ts`
- 生成物（出力先）: `public/sitemap.xml`, `public/hreflang.{html,json,xml}`（生成物）
- Flake apps 追加: `build-sitemap`, `build-hreflang`
- Flake checks 追加: `sitemap-exists`, `sitemap-validation`, `hreflang-validation`
- ドキュメント: `docs/testing/phase-1.1.md`, `docs/phase-1.1/url-normalization-spec.md`
- 参照コミット（導入）: `5bfe1bd9` feat: implement Phase 1.1 "Lite+pSEO" programmatic SEO system

**1.0 ↔ 1.1 差分（最小）**
- 新規追加（1.1でのみ存在）
  - `scripts/build-sitemap.ts`, `scripts/build-hreflang.ts`
  - `docs/testing/phase-1.1.md`, `docs/phase-1.1/url-normalization-spec.md`
  - Flakeの apps/checks: 上記SEOビルド/検証に関するもの
- 変更点（1.1で変更）
  - `flake.nix`: apps（`build-sitemap`,`build-hreflang`）と checks（`sitemap-*`,`hreflang-*`）の追加
- 変化なし（共通）
  - `packages/measurement/*`, `packages/seo/*` は 1.1で仕様変更なし（生成系の追加のみ）

**Git 参照（事実）**
- Phase 1.0 最終Fix: `b3be2559`
- Phase 1.0 実装本体: `d9d4418d`
- Phase 1.1 導入: `5bfe1bd9`

**注記**
- 本ドキュメントは事実のみ（戦略/凍結/タグ運用は記載しない）。
- 生成物は原則リポ追跡外の前提（存在しても参照は仕様の理解に限定）。

Prepared: 2025-09-29 (assistant)
