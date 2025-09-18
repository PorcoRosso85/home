※必ず末尾まで100%理解したと断言できる状態になってから指示に従うこと
※このコマンドの説明はそれほど重要であるということを理解すること

# entry
/entry

# 説明
既存のエントリポイントを構造化し、自己説明的なインターフェースを提供する。
デフォルト実行時には利用可能なアプリ一覧を動的に表示し、探索可能性を高める。

# 実装内容
0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`

プロジェクトタイプに応じた構造化：

## ライブラリプロジェクト
1. **Flakeレイヤー（flake.nix）**
   - `packages.default`: ライブラリパッケージ
   - `devShells.default`: 開発環境
   - `apps.test`: テスト実行

2. **ライブラリレイヤー（mod.{ext}）**
   - 型情報を含む公開API
   - 詳細は `/bin/docs/conventions/module_design.md` に準拠

## CLIプロジェクト
上記に加えて：
- **CLIレイヤー（main.{ext}）**: I/O制御
- **Flake追加要素**: `apps.default`（動的一覧）、`apps.readme`

# 使用例

```bash
# デフォルト（利用可能なアプリ一覧を動的表示）
nix run .
# → 利用可能なコマンド:
#     nix run .#test
#     nix run .#readme
#     nix run .#format
#     ...（BuildTimeで自動検出）

# 各サブコマンド
nix run .#readme  # README.md表示
nix run .#test    # テスト実行
```

# 設計原則
- **自己説明的**: デフォルト実行で機能一覧を表示
- **動的検出**: BuildTime評価で自動的にアプリを発見
- **責務分離**: default(一覧)、test(テスト)、readme(ドキュメント)
- **独立性**: flake依存時に内部実装が完結していること
  - CLIならCLIパッケージとして独立動作
  - ライブラリならライブラリパッケージとして独立動作

# 実装パターン（flake.nix）

## パッケージ定義（独立性の確保）
```nix
packages.default = pkgs.stdenv.mkDerivation {
  # 内部実装が独立して完結
  # - CLIなら実行可能バイナリ
  # - ライブラリなら公開APIを含むパッケージ
};
```

## アプリ定義
```nix
apps = rec {
  default = {
    type = "app";
    program = let
      appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
      helpText = ''
        プロジェクト: <名前>
        
        利用可能なコマンド:
        ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
      '';
    in "${pkgs.writeShellScript "show-help" ''
      cat << 'EOF'
      ${helpText}
      EOF
    ''}";
  };
  
  test = {
    type = "app";
    program = "${pkgs.writeShellScript "test" ''exec pytest -v''}";
  };
  
  readme = {
    type = "app";
    program = "${pkgs.writeShellScript "show-readme" ''cat ${./README.md}''}";
  };
};
```

# 関連ファイル
- /bin/docs/conventions/nix_flake.md（Flakeレイヤーの詳細）
- /bin/docs/conventions/entry.md（エントリーポイント規約）
- /bin/docs/conventions/module_design.md（ライブラリ設計）