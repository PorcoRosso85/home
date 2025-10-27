# ADR 0.11.5: Secrets=唯一入口(手動) / CUE=SSOT / leaf分割 / Guard方針

- **Status**: Proposed
- **Date**: 2025-10-25 (JST)
- **Relates**: ADR 0.11.3（IaC統合）, ADR 0.11.4（sops-nix / flake細粒度 / manifest guard / Terranix）

---

## 0. 決定（確定事項）

### 0.1 Secrets
- **唯一のエントリポイント**として手動管理。
- 外部金庫（Vault等）・R2バックアップは**当面不採用**。
- sops-nixによる暗号化を継続。

### 0.2 CUE=SSOT
- 可能な限り**CUE生成**を優先。
- アーキテクチャ上必須な場合のみ `CUE → (sh/json/yaml)` を生成。
- 逆方向（手書きYAML→CUE）は禁止。

### 0.3 Flakes/leaf
- **leaf出力**で細粒度化。
- 依存は**apps→infra**の一方向のみ。
- サービスは必要leafのみを束ねる。

---

## 1. 背景

**課題**:
- 最小依存での持ち出し・分離容易性を保持したい。
- 機密管理を複雑化せず、単純な手動運用を維持したい。
- CUEを中心とした生成系に統一し、手書き設定ファイルの散乱を防ぎたい。

**目的**:
- 1 VPS = 1 サービスへの分離が容易な構造を維持。
- Secretsの受け渡し・監査を明確化（まず手動で確立、後で自動化検討）。
- CUE中心の宣言的管理により、レビュー基準を明確化。

---

## 2. 影響

### 2.1 Secrets管理
- 手動鍵管理の徹底（ローテーション周期・受け渡し手順は未確定→TODO 3.1）。
- sops-nixで暗号化、復号はactivation時。
- 外部金庫は当面採用しない（シンプル運用優先）。

### 2.2 CUE中心の生成系
- 設定ファイルは原則CUE生成（手書きYAML/JSON禁止）。
- 例外は最小限（アーキテクチャ上必須な場合のみ）。
- CUE→生成の一方向性により、差分レビューが容易化。

### 2.3 leaf細粒度化
- infraはleafパッケージ単位でビルド可能。
- サービス側は必要leafのみを参照（最小依存）。
- apps→infraの一方向依存を厳守（逆依存禁止）。

---

## 3. TODO（未確定事項）

### 3.1 Secrets細部
- ローテーション周期の定義
- 受け渡し手順・監査方法
- 復旧手順の文書化
- 平文検出のCI化

### 3.3 Manifest Guard細部
- 生成物最小セット（CUE中心の構成）
- allowlist配置単位（サービスごと / interfaces配下）
- 比較規則（subset許可 + 禁止キー定義）
- 導入段階（warn先行 → fail移行）

### 3.4 観測バックエンド
- Lokiは検討中（JSONL/R2併用含む）
- OTel Collector導入方針は維持
- 最終選定は別途議論

### 3.5 IaC細部
- R2バケット/キー命名規則
- 最小権限の定義（IAMポリシー）
- provider pin方法
- ロック方法（state backend）

### 3.6 ゾーニング
- ラベル先行→安定後物理移動
- stable昇格条件の定義
- infra/stable / infra/experimental の運用方針

---

## 4. DoD（本PRの完了条件）

1. ✅ 上記「確定」「TODO」が矛盾なく明記されている
2. ✅ 用語統一（sops-nix / Terranix / OpenTofu / R2 / manifest / allowlist / leaf）
3. ✅ 確定とTODOが明確に分離されている
4. ✅ 実装・CI・構成変更を含まない（ドキュメントのみ）

---

## 5. Out of scope

以下は**本PRに含めない**：
- 実装（コード変更）
- CI設定追加・変更
- 新規ディレクトリ追加
- 設定ファイル変更
- 鍵や資格情報の追加

---

## 6. 関連ADR

- **ADR 0.11.3**: リポジトリ構造統一 + IaC統合
- **ADR 0.11.4**: sops-nix / flake細粒度 / manifest guard / Terranix→OpenTofu（R2）
- **ADR 0.11.5**: 本ADR（Secrets=唯一入口 / CUE=SSOT / leaf分割 / Guard方針）
