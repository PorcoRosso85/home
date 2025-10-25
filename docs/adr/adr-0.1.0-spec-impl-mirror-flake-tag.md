# ADR 0.1.0: spec/impl mirror構成 + Nix Flakes参照 + 日付タグ運用

- **Status**: Proposed
- **Date**: 2025-10-25 (JST)
- **Relates**: ADR 0.11.3 / 0.11.4 / 0.11.5 / 0.11.6 / 0.11.7 / 0.11.8
- **Supersedes**: なし（既存ADRと並存、新章の起点）

> **本PRは docs のみ**です。`docs/adr/adr-0.1.0-spec-impl-mirror-flake-tag.md` と `docs/tree.md`（末尾追記）以外を変更しません。
> 実装/CI/ディレクトリ再配置は**後続PR**で扱います。

---

## 0. 背景

- ADR 0.11.3〜0.11.8で4層構造（interfaces/apps/domains/contracts + infra）とCUEガバナンスを確立。
- 本ADRは「仕様(spec)と実装(impl)の**参照入口**」を明文化し、Flakes参照の統一運用を提供（新章0.1.x系の起点）。
- 既存の4層構造は維持。mirror構成は**参照入口のみ**を提供。

## 1. 原則（5原則準拠）

- **SRP**: 仕様と実装の責務分離。mirror入口と4層内部責務は独立。
- **KISS**: シンプルなURL参照テンプレート（`dir=apps/<name>`）。
- **YAGNI**: 実装は必要になるまで行わない。本PRは方針のみ。
- **SOLID/DRY**: 参照入口を一元化、重複排除。

## 2. 決定

### 2.1 mirror構成（参照入口）

```
specification/
  apps/<name>/        # 仕様の入口（契約/方針/ガイド）

apps/
  <name>/             # 実装の入口（コード/flake等）
    ↓ 内部は4層構造に従う
    interfaces/
    apps/
    domains/
    infra/
    policy/
    contracts/
```

**既存4層構造との統合**:
- 4層（interfaces/apps/domains/infra/policy/contracts）は既存通り維持
- mirror構成は`apps/<name>`を**参照入口**として提供
- 内部構造は4層責務に従う（ADR 0.11.3〜0.11.8準拠）

### 2.2 Flakes参照テンプレート

#### 実装→仕様（契約/方針参照）

```nix
inputs.spec.url = "git+https://github.com/<you>/<repo>?ref=partial/specification&dir=apps/<name>";
```

#### 仕様→実装（必要時のみ）

```nix
inputs.app.url = "git+https://github.com/<you>/<repo>?ref=partial/<name>&dir=apps/<name>";
```

**統一運用**:
- 入口は常に`dir=apps/<name>`
- 内部構造は4層責務に従う

### 2.3 ブランチ戦略

- `main`: 安定。直接push不可
- `partial/specification`: 仕様系の下書き・集約
- `partial/<name>`: 個別アプリの部分実装
- `partial/*` → `main` はPR経由（CI承認で自動マージ可）

### 2.4 タグ運用（継続）

- **命名規約**: `spec-<name>-YYYYMMDD[-hhmm]`
- **役割**: 配布点の明示・ロック更新PRの安全トリガ
- **例**: `spec-video-20251025`

### 2.5 CI/ローカル実行方針

- **公式運用**: `push→CIでガード`
- **CIチェック内容**（docs-only想定）:
  - Markdown/リンク健全性（例: markdownlint, lychee）
  - Flakes参照の解決性スモーク（`nix flake show`）
  - 参照例の`dir=apps/<name>`が壊れていないことの簡易チェック
- **ローカル実行**: 任意（CIと同じコマンドで可、規定はしない）

## 3. specification/apps/<name>の責務（例）

### 3.1 契約のソース
```
specification/apps/<name>/cue/schema → contracts/（契約SSOT）
```

### 3.2 方針・規約
```
specification/apps/<name>/policy → policy/（禁止/許可ルール）
```

### 3.3 ツール・補助
```
specification/apps/<name>/tools → codegen/CI補助（apps側で利用）
```

## 4. 非採用（理由）

- **複数リポ分割**: 参照断絶・運用コスト増。初期段階は不採用。
- **"b方式"表記**: 使用しない。「mirror構成＋dir=apps/<name>直参照」に統一。

## 5. 影響範囲

- **docs-only**: 本PRは方針の文書化のみ
- **後続PR**: ディレクトリ再配置・CI実装・実装変更

## 6. リスクと対策

- **参照切れ**: CIで検出（リンク/flake show）。タグ名に日付必須で追跡容易。
- **タグ氾濫**: 命名規約＋PRテンプレで整理。

## 7. 今後の課題（TBD）

- lock-update bot（タグ検出→PR自動化）
- 仕様→実装の逆参照テンプレ整備
- 実装の再格納方針（mirror入口を活かしつつ4層維持）を別PR計画として列挙

## 8. 関連ADR

- ADR 0.11.3（4層構造 + IaC統合）
- ADR 0.11.4（flake細粒度/manifest guard）
- ADR 0.11.5（CUE=SSOT/leaf）
- ADR 0.11.6（Secrets/Guard/IaC/Zoning確定）
- ADR 0.11.7（DoD整合性確認）
- ADR 0.11.8（Manifest責務定義）
