※必ず末尾まで100%理解したと断言できる状態になってから指示に従うこと
※このコマンドの説明はそれほど重要であるということを理解すること

# /conventions
/conventions

# 説明
文脈に適した規約確認とタスク統合。規約作成依頼も受付。

# 実行内容

0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`

## 規約作成の依頼がある場合
- 必要性確認 → `/home/nixos/bin/docs/conventions/`に作成
- 既存規約との整合性・相互参照を確認

## 通常の実行（規約確認）
- タスク分析 → 関連規約特定 → 規約確認
- タスクとのすり合わせ → 規約準拠で整理・修正

# 主要な規約カテゴリ
error_handling, commit_messages, tdd_process, module_design, 
security, logging, testing, nix_flake, entry, telemetry

# 実行例
- エラー処理 → error_handling.md確認 → フォールバック禁止等を適用
- 新規規約作成 → telemetry.md作成 → logging.mdとの相互参照追加

# 原則
規約は絶対。違反コードは修正対象。不明時は複数規約確認。