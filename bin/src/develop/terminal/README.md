# Terminal Development Scripts

## 概要
開発用ターミナルツール群 - 自己完結型のnix shellスクリプト

## スクリプト一覧

### セッション管理
- `./hly` - 開発用tmuxセッション（helix + lazygit + yazi）
- `./aa` - 基本tmuxセッション（shell + watch）

### 検索ツール
- `./search-keys` - bashキーバインド検索（bind設定を対話的に検索）
- `./search-functions` - bash関数検索（宣言済み関数を対話的に検索）
- `./cat-fzf` - ファイル選択表示（fzfでファイル選択→内容表示）

## 使用方法
```bash
# 直接実行（PATHに追加するか、フルパスで実行）
/home/nixos/bin/src/develop/terminal/hly
/home/nixos/bin/src/develop/terminal/aa
/home/nixos/bin/src/develop/terminal/search-keys
/home/nixos/bin/src/develop/terminal/search-functions
/home/nixos/bin/src/develop/terminal/cat-fzf

# または、PATHに追加
export PATH="$HOME/bin/src/develop/terminal:$PATH"
hly                  # 開発環境起動
aa                   # 基本tmux起動
search-keys          # キーバインド検索
search-functions     # 関数検索
cat-fzf             # ファイル選択表示
```

## 特徴
- 各スクリプトが必要な依存関係を自己宣言（shebang内）
- `.config/shell`不要
- `flake.nix`不要
- 最小限の依存関係で高速起動

## スクリプトの仕組み
```bash
#!/usr/bin/env -S nix shell nixpkgs#tmux nixpkgs#helix --command bash
```
このshebangにより、必要なパッケージを自動的に取得して実行します。