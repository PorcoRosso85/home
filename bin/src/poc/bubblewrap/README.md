# Bubblewrap Sandboxing POC

このPOCは、Nix環境でbubblewrapを使用した実際のサンドボックス機能を提供します。

## 使い方

```bash
# SSHキーへのアクセスをブロック
nix run .#run -- cat ~/.ssh/id_rsa

# ネットワークを遮断（strictモード）
nix run .#run -- -p strict curl https://example.com

# 特定ディレクトリに制限（confinedモード）
nix run .#run -- -p confined -w /tmp/myproject make build

# 危険コマンドをブロック（safeモード）
nix run .#run -- -p safe ./untrusted-script.sh

# テスト実行
nix run .#test
```

## プロファイル

- **restricted** (デフォルト): ネットワークOK、ホーム読み取り専用、SSH/GPG鍵アクセス不可
- **strict**: ネットワークなし、ホームアクセスなし、最小権限
- **confined**: 指定ディレクトリ限定、親ディレクトリアクセス不可
- **safe**: 危険コマンド（rm -rf、dd等）ブロック

## Bubblewrap (bwrap) 解説

## 概要
Bubblewrap は、非特権ユーザーでも使えるLinuxサンドボックスツールです。コンテナ技術の軽量版として、プロセスを隔離して実行できます。

## 主な特徴

### 1. 非特権実行
- rootやsudo不要
- 一般ユーザーでサンドボックス作成可能
- setuid不要（user namespacesを使用）

### 2. 軽量
- Dockerのような重いランタイム不要
- 単一のバイナリ
- 起動が高速

### 3. 柔軟な隔離
- ファイルシステム
- ネットワーク
- プロセス空間
- IPC

## 技術的な仕組み

### Linux Namespaces
```
- User namespace: UID/GIDマッピング
- Mount namespace: ファイルシステムビュー
- PID namespace: プロセスID空間
- Network namespace: ネットワークスタック
- UTS namespace: ホスト名
- IPC namespace: プロセス間通信
```

### 基本的な使い方
```bash
# 読み取り専用でバインド
bwrap --ro-bind / / --tmpfs /home bash

# ネットワーク隔離
bwrap --unshare-net --ro-bind / / ping google.com

# 最小限の環境
bwrap \
  --ro-bind /usr /usr \
  --ro-bind /bin /bin \
  --ro-bind /lib /lib \
  --proc /proc \
  --dev /dev \
  --tmpfs /tmp \
  bash
```

## AppArmorとの比較

| 特徴 | Bubblewrap | AppArmor |
|------|------------|----------|
| 動作レベル | ユーザー空間 | カーネル（LSM） |
| 権限要件 | 一般ユーザー | root/sudo |
| 設定方法 | コマンドライン | プロファイルファイル |
| 隔離方法 | Namespaces | パス/権限ルール |
| 可搬性 | Linuxのみ | Linuxのみ |
| 学習曲線 | 低い | 高い |

## 実用例

### 1. Webブラウザの隔離
```bash
bwrap \
  --ro-bind /usr /usr \
  --ro-bind /lib /lib \
  --ro-bind /lib64 /lib64 \
  --ro-bind /bin /bin \
  --ro-bind /etc /etc \
  --proc /proc \
  --dev /dev \
  --tmpfs /tmp \
  --tmpfs $HOME \
  --bind $HOME/Downloads $HOME/Downloads \
  --unshare-all \
  --share-net \
  --die-with-parent \
  firefox
```

### 2. 開発環境の隔離
```bash
bwrap \
  --ro-bind /nix/store /nix/store \
  --bind ./project ./project \
  --tmpfs /tmp \
  --tmpfs /home \
  --setenv HOME /home \
  --unshare-pid \
  --die-with-parent \
  bash
```

### 3. ビルド環境
```bash
bwrap \
  --ro-bind / / \
  --bind ./build ./build \
  --tmpfs /tmp \
  --unshare-net \
  --uid 1000 \
  --gid 1000 \
  make
```

## 利点

1. **即座に使える**
   - インストールするだけ
   - 設定ファイル不要
   - 再起動不要

2. **細かい制御**
   - ファイル単位でアクセス制御
   - 読み取り専用/読み書き可能を選択
   - tmpfsで特定ディレクトリをマスク

3. **開発に最適**
   - テスト環境の隔離
   - 依存関係の分離
   - 安全な実験環境

## 制限事項

1. **Linuxカーネル要件**
   - User namespaces有効化が必要
   - 比較的新しいカーネル（3.8以降）

2. **完全なセキュリティではない**
   - カーネルの脆弱性には対処できない
   - 本番環境では追加の対策が必要

3. **永続性なし**
   - 実行終了でサンドボックス消滅
   - 状態保存には工夫が必要

## Flatpakとの関係
Flatpakは内部でbubblewrapを使用してアプリケーションをサンドボックス化しています。

## まとめ
Bubblewrapは「手軽に使えるサンドボックス」として、開発やテスト、日常的なセキュリティ向上に最適なツールです。AppArmorのような包括的なMACシステムではありませんが、その分シンプルで実用的です。