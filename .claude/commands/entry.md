# entry
/entry

# 説明
既存のエントリポイントを構造化し、自己説明的なインターフェースを提供する。
デフォルト実行時には利用可能なアプリ一覧を動的に表示し、探索可能性を高める。

# 実装内容
既存のflake.nixのエントリポイントを以下のように構造化：

1. **デフォルトアプリ（引数なし）**
   - 利用可能なアプリ一覧を動的に表示
   - BuildTime評価で自動的にアプリを検出
   - プロジェクト固有の使用例を提示

2. **`#test` サブコマンド**
   - プロジェクトのテストスイートを実行
   - 詳細は `/bin/docs/conventions/test_infrastructure.md` に準拠

3. **`#readme` サブコマンド**
   - プロジェクトのREADME.mdを表示
   - 詳細なドキュメントへのアクセスを提供

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

# 実装パターン（flake.nix）

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
- /bin/docs/conventions/nix_flake.md（必須コマンド、動的一覧表示の詳細）