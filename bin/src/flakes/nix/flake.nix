{
  description = "Nix開発環境";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Nix開発ツール群
        nixDevTools = pkgs.buildEnv {
          name = "nix-dev-tools";
          paths = with pkgs; [
            # LSP
            nil
            
            # Formatter
            nixfmt-classic  # nixfmt command
            
            # Linters
            statix
            deadnix
            
            # Development tools
            nix-diff
            nix-du
            
            # Additional tools
            nix-prefetch-git
            nix-tree
          ];
        };
      in
      {
        # パッケージ定義
        packages.default = nixDevTools;
        
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = [ self.packages.${system}.default ];
          
          shellHook = ''
            echo "Nix開発環境"
            echo "利用可能なツール:"
            echo "  - nil: Nix Language Server"
            echo "  - nixfmt: コードフォーマッター"
            echo "  - statix: Nixアンチパターン検出"
            echo "  - deadnix: 未使用コードの検出"
            echo "  - nix-diff: Nix導出の差分表示"
            echo "  - nix-du: Nixストアの使用量分析"
          '';
        };
        
        # アプリケーション
        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                Nix開発環境
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              echo "Nixファイルをフォーマット中..."
              find . -name "*.nix" -type f | while read -r file; do
                echo "Formatting: $file"
                ${pkgs.nixfmt-classic}/bin/nixfmt "$file"
              done
            ''}";
          };
          
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              echo "=== Statix (コード解析) ==="
              ${pkgs.statix}/bin/statix check .
              
              echo -e "\n=== Deadnix (未使用検出) ==="
              ${pkgs.deadnix}/bin/deadnix .
            ''}";
          };
          
          check = {
            type = "app";
            program = "${pkgs.writeShellScript "check" ''
              echo "Nixコードをチェック中..."
              
              # フォーマットチェック
              echo -e "\n=== フォーマットチェック ==="
              find . -name "*.nix" -type f | while read -r file; do
                if ! ${pkgs.nixfmt-classic}/bin/nixfmt --check "$file" 2>/dev/null; then
                  echo "要フォーマット: $file"
                fi
              done
              
              # Lintチェック
              exec ${self.apps.${system}.lint.program}
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              if [ -f README.md ]; then
                cat README.md
              else
                echo "README.mdが見つかりません"
              fi
            ''}";
          };
        };
      });
}