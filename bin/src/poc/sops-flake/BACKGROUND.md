# 背景（sops-nix + flake で機密を扱う設計方針）

本ドキュメントは、sops-nix と Nix flake を前提とした機密情報管理の背景・意図・
運用上の注意点を整理したものです。テンプレート（systemd / user / app-standalone）
や examples（env-encryption）を横断して共通の考え方を示します。

## なぜこの構成が適切か（要点）
- 再現性と分離
  - flake で依存をピン留めし再現性を担保。
  - 機密は sops による「暗号化ファイル」として Git で管理、復号は実行時のみ。
  - 平文を derivation（Nix ストア）へ埋め込まない設計を徹底。
- 最小手順での導入・運用
  - 非 OS 統合（deploy/sliplane 等）: env-encryption で `env.sh.enc` をコミットし、
    `source` で復号・読み込み（導入 ~5 分）。
  - OS 統合（常駐サービス）: sops-nix モジュールで有効化時に秘密ファイルを配置し、
    サービスは `EnvironmentFile` 等で参照。OS 側とアプリ側の責務分離が明確。
- チーム運用が単純
  - 受信者は age を標準、SSH はホスト限定など要件がある場合のみ（ssh-to-age で補助）。
  - どのテンプレートでも同じ初期化フロー（init-template.sh）で開始可能。
- 安全運用の型（ガードレール）が揃っている
  - pre-commit/CI による平文検知（ENC[AES256_GCM] の有無チェック）。
  - `.sops.yaml` の creation_rules とサンプル、ドキュメント／スクリプトの統一。

## 注意すべきポイント（シンプルさを保つコツ）
- 用途ごとに「最短パス」を選ぶ
  - アプリやスクリプト系は env-encryption（`env.sh.enc` をコミット）で十分。
  - 常駐サービスは sops-nix モジュールでファイル展開（derivation に値を埋めない）。
- 受信者は age を標準、SSH は必要時のみ
  - SSH 受信者は依存が増えやすい（`age-plugin-ssh` / `ssh-to-age` など）。
  - 必要性（ホスト限定復号など）が明確な場合だけ採用し、手順を README に明記。
- CI の鍵取り回し
  - `SOPS_AGE_KEY_FILE` もしくは `SOPS_AGE_KEY` を使い、復号はジョブ内でのみ実施。
  - 復号後の一時ファイルは即削除（`shred` など）。
- 環境分離（development/staging/production）
  - ファイル分割（例: `secrets/{development,staging,production}.yaml`）。
  - 共有者変更時は `sops updatekeys` で受信者を更新。
- 「秘密を Nix に埋めない」を徹底
  - 文字列で derivation に渡さない。`config.sops.secrets.<name>.path` や
    systemd の `EnvironmentFile` のような「ファイル参照」で受け渡す。

## よくある運用レシピ（抜粋）
- env-encryption（非 OS 統合）
  - 生成: `./encrypt-env.sh env.sh` → `env.sh.enc` をコミット、`env.sh` は .gitignore。
  - 利用: `source ./source-env.sh env.sh.enc`（CI は `sops -d` で一時展開→source）。
- NixOS サービス（OS 統合）
  - モジュールで `sops.secrets` を宣言し、展開されたパスを `EnvironmentFile` で参照。
  - 受信者は age（標準）／SSH（必要時）を選択。devShell で `sops/age/ssh-to-age` を提供。

## 代替案と本構成の位置づけ
- agenix は NixOS 専用・age 限定でよりシンプルな一面もあるが、
  編集体験や複数バックエンド対応、テンプレ横展開のしやすさは sops-nix が優位。
  本プロジェクトの「多様なテンプレ・ユースケースに即応」という要件に合致。

## 推奨運用（まとめ）
- 現行方針を維持（age デフォルト、SSH は必要時／テンプレは統一済み）。
- CI に「平文検知 + `nix flake check`」を常設。
- 鍵ローテーション（`sops updatekeys`）のミニ手順を各 README に追記。
- 責務分離（OS とアプリ）を徹底し、秘密は常に「ファイル参照」で受け渡す。

