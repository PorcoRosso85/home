# Claude Launcher ストアコピー問題の詳細報告

## 問題の概要

`claude-launcher`の`nix run`実行時に、期待される挙動と異なり、**モノレポ全体（/home/nixos）がNixストアにコピーされる**問題が発生しています。

## 現象

```bash
$ cd /home/nixos/bin/src/develop/claude/ui
$ nix run .
# 出力: "copying /home/nixos to the store"
```

実行時のトレース結果から、モノレポ全体のファイルが読み込まれていることが確認されました：
- `/home/nixos/bin/src/poc/`配下の全ファイル
- `/home/nixos/bin/src/telemetry/`配下の全ファイル
- その他、プロジェクト全体のファイル

## 期待される挙動

「Flakeの階層化と集約」アーキテクチャに従い、以下の挙動が期待されます：

1. **`src = ./.`による範囲限定**: 現在のディレクトリ（`develop/claude/ui/`）のみがコピー対象
2. **高速な起動**: 数MB程度のコピーで済むため、即座に実行開始
3. **キャッシュの有効活用**: 他プロジェクトの変更に影響されない

## 問題の原因

### 1. `writeShellApplication`の暗黙的な挙動

現在の実装では`writeShellApplication`を使用していますが、これは：
- Gitリポジトリのルートまで遡って依存関係を解決
- 結果として`/home/nixos`全体がコピー対象に

### 2. ソースフィルタリングの欠如

他の正しく実装されたプロジェクト（例：`kuzu_py`）では：
```nix
src = ./.;  # 現在のディレクトリのみ
```

しかし、`claude-launcher`ではこの明示的な範囲指定がありません。

## 影響

1. **パフォーマンス**: 起動に数十秒〜数分かかる
2. **ストレージ**: 不要なファイルで数GBを消費
3. **開発効率**: 変更の度に長時間の待機が発生

## 推奨される解決策

### 方法1: buildPythonApplicationへの移行（推奨）

```nix
claudeLauncher = pkgs.python3Packages.buildPythonApplication {
  pname = "claude-launcher";
  version = "0.1.0";
  
  src = ./.;  # 明示的な範囲指定
  
  # または、より厳密なフィルタリング
  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      (pkgs.lib.hasSuffix ".py" path) ||
      (pkgs.lib.hasSuffix ".sh" path) ||
      (type == "directory");
  };
};
```

### 方法2: シェルスクリプトのままフィルタリング

```nix
src = builtins.filterSource
  (path: type:
    # 必要なファイルのみ含める
    (baseNameOf path == "launcher.sh") ||
    (baseNameOf path == "flake.nix")
  )
  ./.;
```

### 方法3: 実行時パス解決への変更

スクリプト内で動的にパスを解決し、ストアコピーを最小化：
```bash
# flakeの検索をランタイムで実行
find "${START_DIR:-$(pwd)}" -name "flake.nix" ...
```

## 検証方法

修正後は以下のコマンドで確認：
```bash
# ストアコピーのメッセージが出ないこと
$ nix run . 2>&1 | grep -v "copying.*to the store"

# または、straceで読み込みファイルを確認
$ strace -e openat nix run . 2>&1 | grep "/home/nixos" | wc -l
# 期待値: 数十件程度（現在: 数千件）
```

## 参考実装

正しく実装されている例：
- `/home/nixos/bin/src/persistence/kuzu_py/flake.nix`
- `/home/nixos/bin/src/architecture/flake.nix`

これらは`src = ./.`により、適切に範囲を限定しています。

## まとめ

この問題は「Flakeの階層化と集約」アーキテクチャの原則に反しており、モノレポでの`nix run`の利点を損なっています。早急な修正により、開発効率の大幅な改善が期待されます。

## 2024年8月 解決事例（更新版）

claude-launcherプロジェクトで、最終的に以下の方法で問題を完全に解決しました：

### 最終解決策: シンプルなdevShellsのみの構成

1. **packagesとappsを完全に削除**
   ```nix
   # flake.nix - devShellsのみ
   {
     outputs = { self, nixpkgs }: {
       devShells.${system}.default = pkgs.mkShell {
         packages = [ fzf findutils ... ];
       };
     };
   }
   ```

2. **重要な発見: devShellsのみならストアコピーは発生しない**
   - `builtins.readFile`を使わない
   - `${./file}`のような参照を使わない
   - packagesやappsを定義しない
   - これらの条件下では、モノレポでも問題なし

3. **nix shellは不要**
   - `nix develop -c ./claude-launcher`で十分
   - ストアコピー問題は発生しない
   - パフォーマンスも実用的（1-4秒）

### 検証結果
- ✅ "copying '/home/nixos/' to store"は発生しない
- ✅ Nixパッケージのダウンロードのみ（初回のみ）
- ✅ 起動時間: キャッシュ済みで1-4秒
- ✅ 最小限の構成で最大の効果

### 結論
**nix shellは完全に不要です。** シンプルなdevShells構成のnix developで、ストアコピー問題なく実用的に動作します。