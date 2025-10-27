<!-- 責務: 本リポの最新ADR。Flake宣言/SSOT仕様/CUE責務、consumes、Secrets必須、SBOM/CVE、監査、パリティ等の規範を定義 -->
# ADR 0.10.11 — Flake駆動マニフェスト / consumes採用 / Secrets必須 / SBOM & CVE / 監査サマリ

- **Status**: Accepted
- **Supersedes**: ADR 0.10.10
- **Date**: 2025-10-23 (JST)
- **Owner**: Platform/Architecture
- **Scope**: contracts/ssot, features/**, deployables/**, tools/{bridge,gates,security,graph,paths-filter}, policy/cue/**, .github/**

---

## 目的（短）

- **Flake＝宣言 / SSOT＝仕様 / CUE＝責務** を固定
- **flake→manifest.cue を決定的生成**（非コミット、差分＝意図）
- **宣言（manifest）と実装（module）をパリティで自動整合**
- **Secrets必須・SBOM/CVE・監査サマリ**で安全と説明責任を確保

---

## 用語

- **feature**: 契約を**提供**（provides）する単位（1機能=1フレーク）
- **deployable**: 実行/デプロイ単位（1プロセス=1フレーク）
- **module**: 実装下位単位（go/py/ts…）
- **contract**: SSOT契約（`domain.subject@semver`）
- **provides**: 提供（feature側。`contractRef` 由来）
- **consumes**: 依存（deployableの宣言／moduleの意図）※`uses`はdeprecated
- **capability**: 契約が提供する個別機能ID（`domain.subject.verb`）

---

## 命名規約

### Capability ID形式

- 形式: `domain.subject.verb`（例: `ugc.post.create`）
- 文字: `[a-z0-9.-]`、1要素≤128、全体≤512
- 重複禁止（`capsules/index.cue` 生成時チェック）

### 関係性: Contract ↔ Capability

**1つの contract**（`<domain>/<subject>@<semver>`）は、**複数の capability**（`<domain>.<subject>.<verb>`）を提供する。

- **所有権**: capability は contract に一意に紐づく（`contractRef` で管理）
- **バージョン**: capability 自体は個別の semver を持たない（破壊的変更は contract の semver で管理）
- **依存**: deployable は capability ID を `consumes` する（例: `["ugc.post.create", "ugc.post.read"]`）

**例**:
```
contract: ugc/post@1.2.0
  ├─ capability: ugc.post.create
  ├─ capability: ugc.post.read
  ├─ capability: ugc.post.update
  └─ capability: ugc.post.delete
```

---

## スキーマ（要点）

### manifest（flake2manifestで生成）

```cue
{
  schemaVersion: >=1
  kind: "feature" | "deployable"
  owner: string
  visibility: "public" | "internal" | "private"
  stability: "experimental" | "beta" | "ga" | "deprecated"

  // feature の場合
  contractRef?: string  // 例: "ugc.post@1.2.0"

  // deployable の場合
  consumes?: [...string]  // 例: ["ugc.post.create", "auth.token.verify"]
}
```

### module（実装側）

```cue
{
  schemaVersion: >=1
  id: string
  lang: string
  role: string
  allowedImports: ["capsules/index"]  // 固定
  intents?: {
    consumes?: [...string]  // 例: ["ugc.post.create"]
  }
}
```

---

## パリティ（宣言↔実装）

### ルール

```
⋃modules.intents.consumes ⊆ manifest.consumes
```

### 目的

宣言を更新せず依存を勝手に増減する行為をブロック

### 既定

**Warn**（必要時にFailへ引き上げ）

---

## 決定性

- **UTC固定** / 安定ソート / 並列数固定 / 乱数seed固定
- `flake2manifest` 出力に**ハッシュ指紋**埋め込み
- 同コミットで一致必須

---

## Secrets / PII

### Secrets検出

- **必須**（鍵/トークン/高エントロピー）
- 検出時は**Fail**

### PII

- **当面オフ**（将来フラグでON可）

---

## SBOM / CVE

### SBOM（Software Bill of Materials）

- 依存の台帳（CycloneDX/SPDX）
- **リリース時に生成** → `.artifacts/reports/sbom.json`

### CVE（Common Vulnerabilities and Exposures）

- 既知脆弱性突合（OSV/NVD）
- **週次＋リリース前** → `.artifacts/reports/cve.json`

---

## Waiver（例外承認）

```cue
{
  targetPath: string  // glob対応
  ruleIds: [...string]
  reason: string
  owner: string
  expiresAt: string  // ISO8601（必須）
}
```

- 期限切れ=**Fail**（Auto-PR推奨）
- **TTLは`sandbox/`向け**。`features/`と`deployables/`はTTL対象外

---

## paths-filter（最小）

- `contracts/ssot/**` → それを**consumes**する feature/deployable のテストを再実行
- `features/<d>/<f>/**` → 当該feature＋それに依存する deployables
- `policy/**`・`tools/gates/**` → 全体（安全）

---

## 監査・可観測性

`.artifacts/reports/summary.json` に集約:
- fail/warn件数
- 重大Top3
- 差分TopN

PRに要約コメント（任意）

---

## CI（最小）

直列:
```
index → flake2manifest → cue vet → gates(secrets/parity/…)
```

- **SBOM**: リリース時
- **CVE**: 週次

---

## DoD（最小）

- ✅ `schemaVersion=1`
- ✅ `cue vet` 合格
- ✅ **決定性ハッシュ一致**
- ✅ **parity=OK**（不一致0）
- ✅ **Secrets=OK**
- ✅ SSOT **stories**: normal/error/boundary 各1
- ✅ 主要レポートが `.artifacts/reports/` に出力

---

## 互換

`uses`は**deprecated**:
- 内部で`consumes`へマップし警告
- 将来`schemaVersion=2`で無効化予定

---

## 変更履歴

- 2025-10-23: 初版（Accepted）
