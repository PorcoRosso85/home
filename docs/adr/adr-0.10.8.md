# ADR 0.10.8 – タグ駆動SSOT + Generator/Gates + Flake修正

- **Status**: Accepted
- **Date**: 2025-10-23 (JST)
- **Owner**: Platform/Architecture
- **Related**: adr-0.10.5-rc3.md（旧構成の参考）

## 0. 結論（要点）
- **SSOT**：`features|deployables/**/manifest.cue` のみ人が編集可。
- **タグ駆動**：`unit|integration|e2e|uat` 等はタグで決定（競合時は**最重タグ優先**、降格不可）。
- **生成一貫**：`gen/tests|seeds|docs` は **生成のみ**。fingerprint不一致は **CI Fail**。
- **テスト実行**：`pytest` / `go test` は置換せず、**runner（薄いラッパ）** が呼び出す。
- **contracts-index**：flakeで**決定的生成**、参照は常に `import "capsules/index"`。直 import 禁止。
- **外部出力**：`dist/contracts/**` に **OpenAPI/AsyncAPI/Schema + Auth/RateLimit/Errors** をCIで書き出し。
- **ガバナンス**：**PIIマスク必須**、暗号化/TTL/署名は条件付き必須。
- **flake修正**：ルート`flake.nix`のゴミ文字を除去（P0）。

## 1. 背景
- 旧PR（構造雛形）では「phase別ディレクトリ」や未実装のゲートが混在し、決定性・運用基準が弱かった。
- 本ADRで **タグ駆動SSOT** と **生成一貫**、**品質ゲート** を採用し、変更管理を強化。

## 2. 決定（MUST/SHOULD）
- **MUST**：SSOTはmanifest.cueのみ／`gen/**` 手書き禁止／`capsules/index.cue` 非コミット。
- **MUST**：flakeでindexを**決定的**生成（同一`flake.lock`でバイト等価）。
- **MUST**：`import "capsules/index"` のみ許可（直 import 禁止）。
- **MUST**：各manifestに **cases≥3（正常/失敗/境界）** を含む。
- **SHOULD**：エラーカタログ・RateLimit・非機能閾値（p95/err率）を明記。
- **SHOULD**：runnerは言語ごとの**language-pack**から呼び出す（Py/Go）。

## 3. スコープ
- generator／language-packs／gates／contracts-index（flake）／CI／`dist/contracts/**` 出力。

## 4. 非対象
- 実行時のURL/資格情報/プロビジョニング詳細。
- 既存pytest/goテスト本体の置換（ラッパで呼ぶのみ）。

## 5. 品質ゲート（例）
- `quality`：cases≥3、waiverにTTL必須。
- `banned-tags`：未許可・降格タグ検出。
- `contract-diff`：SemVer整合／破壊差分検知。
- `cap-dup`：capability一意制約。
- `plan-diff`：依存・影響差分。
- `determinism`：UTC/RNG/ID/TZ/順序/JSON正規化。
- `golden-ttl`：変動源のゴールデン更新期限。
- `mask`：**PIIマスク**確認。
- 旧系：`lint contracts`（L100–L104互換）も維持。

## 6. CIパイプライン（骨子）
- `build(index)` → `cue vet` → `gen run` → `gen check` → `gates` → `runner`
- PR：`unit + @smoke`／Merge：`integration`／Nightly：`e2e+perf/sec`／Release：`uat`

## 7. DoD（受入基準）
- 同一`flake.lock`で **contracts-indexがバイト等価**。
- **fingerprint一致**（manifest ↔ gen/**）。
- L100–L104=0、**PIIマスクOK**、**banned-tagsなし**、**determinism OK**。
- `dist/contracts/**` が生成され、破壊差分は `contract-diff` でFail。

## 8. 移行手順（短）
1. 旧「phase別dir」を廃止し、**タグ駆動**へ統一。
2. `.gitignore` 強化（`gen/**`, `capsules/index.cue`）。
3. `flake.nix` のゴミ文字を修正→ `nix build .#contracts-index` が通ること。
4. `tools/generator` / `tools/language-packs/{python,go}` を追加。
5. 代表機能（例：`features/ugc/post`）からmanifest→gen→gates→runnerの順で適用。

## 9. バックアウト
- 一時的に `banned-tags`/`determinism` を **WARNING** 化。
- generatorの `gen check` を一時スキップ（要期限）。
- `dist/contracts/**` 出力は継続（公開インタフェースの透明性維持）。

## 10. セキュリティ/ガバナンス
- **PIIマスク必須**（検出→Fail）。
- 暗号化/TTL/署名：データ種別・環境タグに応じて**条件付き必須**。
- RateLimit・エラーカタログ・連絡先(owner/contact)をmanifestに明記。

## 11. トレードオフ
- 初期コスト：generator/ゲート整備が必要。
- 代償：手書き自由度低下。ただし決定性と保守性が向上。

## 12. 用語
- **SSOT**：Single Source of Truth（manifest.cue）。
- **language-pack**：テスト実行ラッパ（Py/Go）。
- **fingerprint**：生成物とmanifestの同一性指紋。

## 13. 変更履歴
- 2025-10-23: 初版（Accepted）
