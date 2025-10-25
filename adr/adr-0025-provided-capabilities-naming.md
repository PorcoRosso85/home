# 提供機能の命名規則

## ステータス
Proposed

## 文脈
- アプリケーションの提供機能(capabilities)を一貫した命名で管理したい。
- ドメイン機能中心の命名で、同義語・表記揺れ・粒度差異による負債を避ける。
- これまでの ADR と tree.md の構成に整合する形で、ルールの配置と適用方法を定める。

## 決定
1. **命名の基本単位**: "ドメイン機能名" を英小文字ケバブケース(kebab-case)で表す。例: `accounting`, `inventory-management`, `order-sync`.
2. **接頭辞の扱い**: 供給形態を示す接頭辞は原則付けない（UI/API/Batch等は"利用チャネル"で管理する）。
3. **スコープの表現**: 範囲を区別したい場合は `:` 区切りで下位概念を連結する。例: `inventory-management:replenishment`.
4. **禁止事項**: 時間・環境・人名・プロジェクト名は付けない（"本質的な機能"のみ）。例: `-2025`, `-prod`, `-suzuki`, `-phoenix` は不可。
5. **正規語彙**: `policy/cue/domain_vocabulary.cue` に正規語彙(許可リスト)を定義し、
   - 同義語の正規化(例: `stock`→`inventory`)、
   - 省略形の展開(例: `inv-mgmt`→`inventory-management`)、
   - 使用禁止語の検出を行う。
6. **確認手段**: `cue vet` により `tree.md` とコード上の `capabilities` フィールドを検証するスクリプトを追加する（別PR）。

## 根拠
- ドメイン駆動での語彙統一は検索性・再利用性・可観測性を高める。
- チャネル(UI/API/Batch)や層(APP/Domain/Infra)を名前に混ぜると寿命が短くなる。
- CUE による語彙制約は"破ると落ちる"を実現でき、運用コストが低い。

## 影響範囲
- `tree.md` の `capabilities` 記載。
- ADR/設計文書の見出し・タグ。
- モジュール名・イベント名の一部（該当時）。

## 代替案
- ディレクトリや接頭辞でチャネルを区別する案（柔軟性が低く却下）。
- スネーク/パスカル/キャメル等のケース統一（ケバブがUI・URL・タグで扱いやすい）。

## 実装計画
- 本PRでは ADR の追加のみ。
- 後続で `policy/cue/domain_vocabulary.cue` と `scripts/cue-validate-capabilities.sh` を追加する。

## 付録: サンプル語彙（暫定）
```
allowed: [
  "accounting", 
  "inventory-management", 
  "order-sync", 
  "customer-support"
]
forbidden: [
  "stock", 
  "inv-mgmt", 
  "phoenix"
]
normalize: {
  "stock": "inventory-management",
  "inv-mgmt": "inventory-management"
}
```
