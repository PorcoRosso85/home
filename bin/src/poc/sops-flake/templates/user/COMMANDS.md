# コマンドリファレンス - User Template

## 初期化

| コマンド | 説明 |
|---------|------|
| `./scripts/init-template.sh` | テンプレート完全初期化（Age鍵生成、.sops.yaml設定、Git hooks） |
| `./scripts/setup-age-key.sh` | Age鍵生成/確認（既存鍵がある場合は公開鍵表示） |
| `./scripts/setup-ssh-recipient.sh` | SSH鍵をSOPS受信者として設定 |

## 開発

| コマンド | 説明 |
|---------|------|
| `nix develop` | 開発環境起動（sops、nixコマンド利用可能） |
| `nix flake check` | Flake検証（構文とビルド可能性チェック） |
| `nix build` | Home Managerモジュールビルド実行 |
| `nix build .#homeConfigurations.test.activationPackage` | テスト用Home Manager構成ビルド |

## シークレット管理

| コマンド | 説明 |
|---------|------|
| `sops edit secrets/app.yaml` | シークレット編集（暗号化されたファイルを復号化して編集） |
| `sops decrypt secrets/app.yaml` | 一時復号化（内容確認用） |
| `sops -e -i secrets/app.yaml` | 手動暗号化（平文ファイルを暗号化） |
| `./scripts/verify-encryption.sh` | 暗号化確認（secrets/内全ファイルの暗号化状態チェック） |
| `./scripts/check-no-plaintext-secrets.sh` | 平文シークレットチェック（Git commit前の検証） |
| `sops updatekeys secrets/app.yaml` | 暗号化鍵更新（新しい公開鍵を.sops.yamlに追加後） |

## SSH受信者管理
| コマンド | 説明 |
|---------|------|
| `./scripts/setup-ssh-recipient.sh` | SSH鍵をSOPS受信者として設定 |
| `ssh-to-age -i ~/.ssh/id_ed25519.pub` | SSH公開鍵をage形式に変換 |
| `ssh-to-age -i ~/.ssh/id_rsa.pub` | SSH鍵のRSA版変換 |

## デプロイ（Home Manager統合）

| コマンド | 説明 |
|---------|------|
| `home-manager switch` | ユーザー環境の再構築とツール有効化 |
| `home-manager build` | ビルドのみ（アクティブ化はしない） |
| `home-manager news` | Home Manager変更履歴確認 |
| `home-manager generations` | 世代一覧表示 |
| `home-manager rollback` | 前の世代にロールバック |

## デプロイ（NixOS統合 - システムワイド）

| コマンド | 説明 |
|---------|------|
| `sudo nixos-rebuild switch` | システム全体の再構築（ユーザーツールとして利用可能に） |
| `sudo nixos-rebuild test` | テスト用再構築（再起動で元に戻る） |
| `sudo nixos-rebuild dry-run` | 変更内容のプレビュー |

## ツール実行

| コマンド | 説明 |
|---------|------|
| `my-tool` | ツール実行（Home Manager switchまたはnixos-rebuild switch後） |
| `my-tool backup` | バックアップコマンド実行例 |
| `my-tool sync` | 同期コマンド実行例 |
| `my-tool status` | ステータス確認コマンド例 |
| `my-tool --help` | ヘルプ表示 |

## サービス管理（タイマー有効時）

| コマンド | 説明 |
|---------|------|
| `systemctl --user status my-tool.timer` | ユーザータイマー状態確認 |
| `systemctl --user start my-tool.timer` | タイマー開始 |
| `systemctl --user stop my-tool.timer` | タイマー停止 |
| `systemctl --user enable my-tool.timer` | タイマー自動起動有効化 |
| `systemctl --user disable my-tool.timer` | タイマー自動起動無効化 |
| `systemctl --user list-timers` | アクティブなタイマー一覧 |
| `journalctl --user -u my-tool -f` | リアルタイムログ確認 |
| `journalctl --user -u my-tool --since="1 hour ago"` | 過去1時間のログ確認 |

## トラブルシューティング

| コマンド | 説明 |
|---------|------|
| `nix flake show` | Flakeの出力確認（利用可能なパッケージ・モジュール一覧） |
| `nix flake update` | 依存関係更新（flake.lock更新） |
| `nix show-derivation` | ビルド設定詳細表示 |
| `age-keygen -y ~/.config/sops/age/keys.txt` | Age公開鍵確認 |
| `echo $SOPS_AGE_KEY_FILE` | SOPS鍵ファイル設定確認 |
| `sops --version` | SOPSバージョン確認 |
| `home-manager --version` | Home Managerバージョン確認 |
| `which my-tool` | ツールのパス確認 |

## Git管理

| コマンド | 説明 |
|---------|------|
| `git add secrets/app.yaml .sops.yaml` | 暗号化ファイルと設定をステージング |
| `git status` | 平文ファイルが誤ってステージングされていないかチェック |
| `git commit -m "feat: add encrypted secrets"` | 暗号化ファイルのコミット |
| `git log --oneline secrets/` | シークレット変更履歴確認 |

## テスト・検証

| コマンド | 説明 |
|---------|------|
| `nix eval .#homeManagerModules.default` | Home Managerモジュール構造確認 |
| `home-manager build --dry-run` | ビルド予定の確認 |
| `systemd-analyze --user verify ~/.config/systemd/user/my-tool.service` | ユーザーサービスファイル検証 |

## 設定確認

| コマンド | 説明 |
|---------|------|
| `nix show-config` | Nix設定確認 |
| `systemctl --user cat my-tool` | 生成されたユーザーサービス確認 |
| `systemctl --user list-unit-files \| grep my-tool` | ユニットファイル状態確認 |
| `home-manager packages` | インストールされたパッケージ一覧 |

## 環境情報

| コマンド | 説明 |
|---------|------|
| `uname -a` | システム情報 |
| `nix --version` | Nixバージョン |
| `systemctl --version` | systemdバージョン |
| `which sops age` | 必要ツールのパス確認 |
| `echo $HOME` | ホームディレクトリ確認 |