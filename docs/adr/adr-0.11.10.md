# ADR 0.11.10: Capability重複検知と依存アドバイザ（Draft）
- **Status**: Draft
- **Date**: 2025-10-25 (JST)
- **Relates**: ADR 0.11.4 / 0.11.5 / 0.11.6 / 0.11.7 / 0.11.8
- **Supersedes**: なし（0.11.8の方針を具体化）

## 0. 背景
- 0.11.8 で Manifest 責務（`provides/consumes/redundant`）と Capability ガバナンス方針を文書化。
- 0.11.9 で命名統一（manifest vs contract）を議論予定。
- 本ADR (.10) は、**重複の自動阻止**と**依存アドバイス**を実装レベルに落とす。

## 1. 決定（Draft）
1) **重複検知（capability-dup）** を CI の gate に導入。
2) **依存アドバイス（dep-advisor）** を `nix flake check`/`nix run` で提供。

## 2. 仕様（Draft）
### 2.1 データ語彙
- `capability-id: #CapID`（正規表現: `^[a-z][a-z0-9.-]+$`）
- `exclusive: bool` / `scope: "repo"|"zone"|"env"`
- `redundant: { reason: "migration"|"canary"|"ha", ttlDays?: int }`

### 2.2 ルール
- `capability-dup`: 同一 `#CapID` かつ `exclusive==true` が同一 `scope` 内で多重→ **gate**。`redundant` 許容は `ttlDays` 残日≤14で **warn**、超過で **fail**。
- `consumes-covered`: すべての `consumes[*]` は repo 内いずれかの `provides[*]` に**被覆**される。未被覆は **gate**。
- `deps-allowed`: `deps.cue` の許可行列を超える flake 参照を **gate**。

### 2.3 CI 連携
- `checks.<sys>.capability-dup` / `checks.<sys>.dep-advisor` を追加（`cue vet/eval` と突合）。
- レポート：人間可読（表/差分）＋ 機械可読（JSONL）。

## 3. スコープ外（Draft）
- 近似一致辞書のメンテ方法、allowlistの承認フロー、提示スコア式の最適化。

## 4. 影響（Draft）
- CI 実行時間 +5% 以内。
- 既存 flake/manifest に `provides/consumes` を追補する必要あり。

## 5. 移行（Draft）
- 適用直後は **warn** に設定、2スプリント後に **fail** へ格上げ。

## 6. 代替案
- CLI のみ（Gate無し）→ レポート閲覧だけ。採用せず（抑止力が弱い）。

## 7. 未決事項
1) 近似一致の閾値/辞書の責任。
2) インデックスの保管場所。
3) allowlistの期限切れ自動失効。
4) 提示順位の評価式。

> `.9` の命名結論に追従して用語調整予定。
