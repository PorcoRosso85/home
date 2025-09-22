# just-every-code — 最小flake + 実ブラウザ操作（CDP）

目的は「最小限のflakeによる環境を用意」し、Chrome DevTools Protocol（CDP）で実際にブラウザを操作することです。本リポジトリには、CDPで接続するための最小ツール一式を用意しています。

- CDP対応＝実ブラウザを直接操作（ページ遷移・DOM操作・JS実行・スクショ等）
- 外部のChrome/ChromiumにCDPで接続（`/chrome`）と、内蔵ヘッドレスChromiumを起動して接続（`/browser`）の両方をサポート
- 使い方は CLI からシンプルに実行

注意: 各サイト/プロバイダの利用規約・レート制限に従ってください。ログインやスクレイピングの禁止事項がある場合は厳守してください。

## セットアップ（Nix Flake）

```bash
nix develop
```

**注意**: Git未追跡パスでエラーが出る場合は以下のいずれかを実行：

```bash
# 方法1: 未追跡パスを許可（推奨）
nix develop --impure 'path:.'

# 方法2: プロジェクトをGit管理下に置く
git add .
nix develop
```

これで以下が使える devShell が入ります：

- `chromium`（または unfree で `google-chrome` に切替可能）
- `python3` + `websocket-client`（CDPを話す簡易スクリプト用）

devShell では、`artifacts/` と `.chromium-profile/` のディレクトリが自動作成されます。

## 実ブラウザに接続（/chrome）

既に起動中の Chrome/Chromium に CDP で接続します。まず外部ブラウザをリモートデバッグで起動します。

例: Chromium（ログイン状態の持続用にプロファイルを指定）

```bash
chromium \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=$(pwd)/.chromium-profile \
  --no-first-run --no-default-browser-check
```

例: Google Chrome（unfree を有効にした環境で）

```bash
google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=$(pwd)/.chromium-profile \
  --no-first-run --no-default-browser-check
```

**重要**: /chromeモードでは以下に注意してください：

1. **Origin一致**: 環境変数`JUST_EVERY_CODE_ALLOW_ORIGINS`と外部ブラウザの`--remote-allow-origins`設定を一致させる
2. **本番環境**: `--remote-allow-origins=*`は開発専用。本番では固定ポート+厳密originを推奨
3. **セキュリティ**: 外部ブラウザの起動設定は、環境変数ではなく手動で管理する必要がある

次に、CDP デモスクリプトで接続・操作します（ラッパー `bin/just-every-code` も用意）。

```bash
# 別シェルで nix develop に入ってから（どちらでも可）
python tools/cdp_minimal.py /chrome 9222 https://example.com
# もしくは
./bin/just-every-code /chrome 9222 https://example.com
```

出力:

- ページタイトルを取得
- `artifacts/screenshot.png` にスクリーンショット保存

## 内蔵ヘッドレスで起動（/browser）

Chromium をヘッドレスで起動し、自動で CDP に接続して操作します（追加のブラウザ起動は不要）。

```bash
nix develop
python tools/cdp_minimal.py /browser https://example.com
# もしくは
./bin/just-every-code /browser https://example.com
```

同様に、タイトル取得と `artifacts/screenshot.png` を出力します。

## できること・メモ

- 代替しやすい: ページ巡回、入力・クリック（CDPコマンド拡張で）、スクリーンショット、Runtime.evaluate での JS 実行、Network 監視 等
- 工夫が要る: ログインの長期維持（プロフィール/クッキー永続化の設計）、2FA/SSO/CAPTCHA は人手介入や専用実装が必要
- 高度な自動探索・戦略: 本スクリプトは最低限。必要に応じて MCP/Playwright 等を組み合わせると強化可能

## コマンド対応（概念）

- `/chrome <port> [url]` … 既存ブラウザに CDP 接続
- `/browser [url]` … ヘッドレスChromiumを内部起動して CDP 接続

内部では CDP の `Target.createTarget` → `Target.attachToTarget` → `Page.navigate` → `Runtime.evaluate` → `Page.captureScreenshot` を呼び出しています。

## 環境変数によるセキュリティ制御

### 環境変数一覧

- `JUST_EVERY_CODE_ALLOW_ORIGINS`: Chrome起動時の `--remote-allow-origins` 設定
- `JUST_EVERY_CODE_WS_ORIGIN`: WebSocket接続時の `origin` パラメータ設定

### 開発環境での使用例

```bash
# デフォルト（開発時推奨）- あらゆるoriginを許可
./bin/just-every-code /browser https://example.com

# 明示的な設定
export JUST_EVERY_CODE_ALLOW_ORIGINS="*"
./bin/just-every-code /browser https://example.com
```

### 本番環境での推奨設定

```bash
# 固定ポート + 厳密origin（本番推奨）
export JUST_EVERY_CODE_ALLOW_ORIGINS="http://127.0.0.1:9222"
export JUST_EVERY_CODE_WS_ORIGIN="http://127.0.0.1:9222"

# /chromeモードで外部ブラウザを固定ポートで起動
chromium --remote-debugging-port=9222 --remote-allow-origins=http://127.0.0.1:9222 \
  --user-data-dir=$(pwd)/.chromium-profile --no-first-run --no-default-browser-check

# 接続実行
./bin/just-every-code /chrome 9222 https://example.com
```

**重要**: /chromeモードでは、外部ブラウザ起動時と環境変数設定で **originを一致させる** 必要があります。

## 参考

- Chrome DevTools Protocol 公式: https://chromedevtools.github.io/devtools-protocol/
- リモートデバッグ起動オプション: `--remote-debugging-port`, `--user-data-dir`

## 利用上の注意

- 各サービスの利用規約/robots/レート制限の遵守は必須です。
- セッション/クッキーの長期保持は、`--user-data-dir` プロファイル活用が有効です。
- 2FA/SSO/CAPTCHA/ボット検知があるサイトは、人手介入や追加ロジックが必要なことが多いです。
