{
  description = "Common Python environment for bin/src projects";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      # Overlay定義 - Python パッケージ拡張用
      overlay = final: prev: {
        pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
          (python-final: python-prev: {
            # 将来的にカスタムPythonパッケージをここに追加
          })
        ];
      };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];
        };
        
        # 共通のPython環境
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pytest
          pytest-json-report
        ]);
      in
      {
        # パッケージ提供
        packages = {
          # 共通のPython環境を提供
          pythonEnv = pythonEnv;
          
          # 開発ツール
          pyright = pkgs.pyright;
          ruff = pkgs.ruff;
          
          # Vessel - 分析スクリプト実行の器
          vesselPyright = pkgs.writeShellScriptBin "vessel-pyright" ''
            #!${pkgs.bash}/bin/bash
            export PATH="${pkgs.pyright}/bin:$PATH"
            ${pkgs.python312}/bin/python3 ${./infrastructure/vessel_pyright.py}
          '';
          
          vesselPython = pkgs.writeShellScriptBin "vessel-python" ''
            #!${pkgs.bash}/bin/bash
            export PATH="${pythonEnv}/bin:${pkgs.pyright}/bin:${pkgs.ruff}/bin:$PATH"
            ${pkgs.python312}/bin/python3 ${./infrastructure/vessel_python.py}
          '';
        };
        
        # 実行可能アプリケーション
        apps = rec {
          # デフォルト - 利用可能なコマンドを動的に表示
          default = {
            type = "app";
            program = let
              # ビルド時に利用可能なアプリ名を取得
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                プロジェクト: Python共通環境 (bin/src/flakes/python)
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
                
                開発環境:
                  nix develop
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          # テスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "Python環境のテストツール:"
              echo ""
              echo "pytest version:"
              ${pythonEnv}/bin/pytest --version
              echo ""
              echo "pyright version:"
              ${pkgs.pyright}/bin/pyright --version
              echo ""
              echo "ruff version:"
              ${pkgs.ruff}/bin/ruff --version
            ''}";
          };
          
          # README表示
          readme = {
            type = "app";
            program = let
              # README.mdの存在を事前にチェック
              readmeExists = builtins.pathExists (./. + "/README.md");
              readmeContent = if readmeExists then builtins.readFile ./README.md else "";
            in "${pkgs.writeShellScript "show-readme" ''
              ${if readmeExists then ''
                cat << 'EOF'
                ${readmeContent}
                EOF
              '' else ''
                # README.mdが存在しない場合のデフォルトメッセージ
                cat << 'EOF'
# Python共通環境

bin/src配下のPythonプロジェクトで使用する共通環境を提供します。

## 提供する環境
- Python 3.12
- pytest (テストフレームワーク)
- pytest-json-report (テスト結果JSON出力)
- pyright (型チェッカー)
- ruff (リンター/フォーマッター)

## 使用方法
子プロジェクトのflake.nixで以下のように参照:

```nix
inputs.python-flake.url = "path:/home/nixos/bin/src/flakes/python";
```

## Vesselツール
- vessel-pyright: Pyright分析スクリプトの実行環境
- vessel-python: Pythonテストスクリプトの実行環境

詳細は examples/ ディレクトリを参照してください。
EOF
              ''}
            ''}";
          };
          
          # Vessel実行
          vessel-pyright = {
            type = "app";
            program = "${self.packages.${system}.vesselPyright}/bin/vessel-pyright";
          };
          
          vessel-python = {
            type = "app";
            program = "${self.packages.${system}.vesselPython}/bin/vessel-python";
          };
        };
        
        # 開発シェル
        devShells = {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              pythonEnv
              pyright
              ruff
            ];
            
            shellHook = ''
              echo "Python開発環境へようこそ"
              echo ""
              echo "利用可能なツール:"
              echo "  - python (${pythonEnv}/bin/python)"
              echo "  - pytest"
              echo "  - pyright"
              echo "  - ruff"
              echo ""
              echo "Vesselツール:"
              echo "  - vessel-pyright: Pyright分析の器"
              echo "  - vessel-python: Pythonテスト実行の器"
            '';
          };
          
          # Pyright専用環境
          pyright = pkgs.mkShell {
            buildInputs = with pkgs; [
              python312
              pyright
            ];
          };
          
          # Python実行環境
          python = pkgs.mkShell {
            buildInputs = with pkgs; [
              pythonEnv
              pyright
              ruff
            ];
          };
        };
        
        # Overlay提供
        overlays.default = overlay;
      }) // {
        # システム非依存のoverlayも提供
        overlays.default = overlay;
      };
}
