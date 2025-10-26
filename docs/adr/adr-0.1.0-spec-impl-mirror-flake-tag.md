# ADR 0.1.0: spec/impl mirror構成 + Nix Flakes参照 + 日付タグ運用（自動ディスカバリ制）

- **Status**: Accepted
- **Date**: 2025-10-25 (JST)
- **Relates**: ADR 0.11.3 / 0.11.4 / 0.11.5 / 0.11.6 / 0.11.7 / 0.11.8
- **Supersedes**: なし（既存ADRと並存、新章の起点）

> **本PRは docs のみ**です。`docs/adr/adr-0.1.0-spec-impl-mirror-flake-tag.md` と `docs/tree.md`（末尾追記）以外を変更しません。
> 実装/CI/ディレクトリ再配置は**後続PR**で扱います。

---

## 0. 背景

- ADR 0.11.3〜0.11.8で4層構造（interfaces/apps/domains/contracts + infra/policy）とCUEガバナンスを確立。
- 本ADRは「仕様(spec)の**参照入口**」を明文化し、Flakes参照の統一運用を提供（新章0.1.x系の起点）。
- **repo直下の4層構造は維持**。mirror構成は`specification/`配下の**参照入口のみ**を定義。

## 1. 原則（5原則準拠）

- **SRP**: 仕様と実装の責務分離。参照入口と4層内部責務は独立。
- **KISS**: シンプルなURL参照テンプレート（`dir=<entrypath>`自動ディスカバリ制）。
- **YAGNI**: 実装は必要になるまで行わない。本PRは方針のみ。
- **SOLID/DRY**: 参照入口を一元化、重複排除。

## 2. 決定

### 2.1 参照規約（自動ディスカバリ制）

#### 基本原則

```
specification/
  apps/[<scope>/]<name>/       { flake.nix, cue/**, tools/** }
  contracts/<name>/            { flake.nix, … }
  infra/<name>/                { flake.nix, … }
  interfaces/<name>/           { flake.nix, … }
  domains/<name>/              { flake.nix, … }

# repo直下の 4層（interfaces/apps/domains/infra/policy/contracts）は現行維持
```

**`<entrypath>`定義**:
- `specification/**` 配下で「**直下に flake.nix を持つ任意ディレクトリ**」
- 形式: `<layer>/[<scope>/]<name>` （scopeは任意）
- 命名: kebab-case
- 重複: 禁止（CIが検知）

**例**:
- `apps/video`, `apps/core/video` （scopeは任意）
- `contracts/http`, `infra/runtime`, `interfaces/gateway`, `domains/common`

**禁止**:
- `path:` の常用
- `specification/**` 外への直参照
- `flake.nix` 不在パスへの直参照

### 2.2 Flakes参照テンプレート

#### 実装→仕様（契約/方針参照）

```nix
inputs.spec.url = "git+https://github.com/<you>/<repo>?ref=partial/specification&dir=<entrypath>";
```

**例**:
```nix
# apps層（scopeは任意）
inputs.spec-video.url = "git+https://github.com/<you>/<repo>?ref=partial/specification&dir=apps/video";
inputs.spec-core-video.url = "git+https://github.com/<you>/<repo>?ref=partial/specification&dir=apps/core/video";

# 共有層
inputs.contracts-http.url = "git+https://github.com/<you>/<repo>?ref=partial/specification&dir=contracts/http";
inputs.infra-runtime.url = "git+https://github.com/<you>/<repo>?ref=partial/specification&dir=infra/runtime";
```

#### 仕様→実装（必要時のみ）

```nix
inputs.app.url = "git+https://github.com/<you>/<repo>?ref=partial/<entrypath('/'→'-')>&dir=<entrypath>";
```

### 2.3 ブランチ戦略

- `main`: 安定。直接push不可
- `partial/specification`: 仕様系の下書き・集約
- `partial/<entrypath('/'→'-')>`: 個別アプリ/コンポーネントの部分実装
  - 例: `partial/apps-video`, `partial/apps-core-video`, `partial/contracts-http`
- `partial/*` → `main` はPR経由（CI承認で自動マージ可）

### 2.4 タグ運用

#### 形式
```
spec-<entrypath ('/'→'-' 変換)>-YYYYMMDD[-hhmm]
```

#### 例
- `spec-apps-video-20251026` （scopeなし）
- `spec-apps-core-video-20251026` （scopeあり）
- `spec-contracts-http-20251026-0930`
- `spec-infra-runtime-20251026`

#### 役割
- 配布点の明示
- `flake.lock` 更新PRの安全トリガ（自動化は将来）

### 2.5 統一規則

#### 命名
- 形式: `<layer>/[<scope>/]<name>` （scopeは任意）
- kebab-case を使用
- 重複禁止（CIが検知）

#### 公開の最小契約
- 各`<entrypath>`の`flake.nix`は **packages/checks（+必要ならdevShells）**のみ公開

### 2.6 CI/ローカル実行方針

#### 公式運用
- `push→CIでガード`

#### CIチェック内容（docs-only時は将来実装）

1. **ロック整合性**:
   - `nix flake lock --check`
   - `nix flake check`
   - `inputs.*.url` の `path:` 禁止

2. **エントリ検証**:
   - `dir=<entrypath>` が `specification/**` に存在するか
   - その直下に `flake.nix` があるか
   - なければ fail

3. **重複検出**:
   - `specification/<layer>/**` で同名 `<name>` の衝突があれば fail
   - kebab-case 違反があれば fail

4. **lock-only原則**:
   - ロック更新PRは `flake.lock` 以外の差分があれば fail

#### ローカル実行
- 任意（CIと同じコマンドで可、規定はしない）

## 3. 互換・影響

### 3.1 既存ADRとの関係
- **非衝突**: 既存0.11.xの方針（4層・ポリシー等）とは独立
- **責務**: 本ADRは参照入口と参照規約のみを定義

### 3.2 移行
- 既存の `apps/<scope>/<service>` 形式はそのまま有効（scopeは任意）
- 新規追加時は `<layer>/[<scope>/]<name>` の統一規則に従う

## 4. 非採用（理由）

- **複数リポ分割**: 参照断絶・運用コスト増。初期段階は不採用。
- **略語・"b方式"等**: 使用しない。「mirror構成＋dir=<entrypath>直参照」に統一。
- **標準/例外の区別**: 不採用。自動ディスカバリ制に一本化。

## 5. 影響範囲

- **docs-only**: 本PRは方針の文書化のみ
- **後続PR**: ディレクトリ再配置・CI実装・実装変更

## 6. リスクと対策

- **参照切れ**: CIで検出（エントリ検証・flake check）。タグ名に日付必須で追跡容易。
- **タグ氾濫**: 命名規約＋PRテンプレで整理。

## 7. 今後の課題（TBD）

- lock-update bot（タグ検出→PR自動化）
- 実装の再格納方針（mirror入口を活かしつつ4層維持）を別PR計画として列挙

## 8. 関連ADR

- ADR 0.11.3（4層構造 + IaC統合）
- ADR 0.11.4（flake細粒度/manifest guard）
- ADR 0.11.5（CUE=SSOT/leaf）
- ADR 0.11.6（Secrets/Guard/IaC/Zoning確定）
- ADR 0.11.7（DoD整合性確認）
- ADR 0.11.8（Manifest責務定義）
