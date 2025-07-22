{
  description = "Dynamic app listing test";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        apps = rec {
          # デフォルトアプリで動的にアプリ一覧を表示
          default = {
            type = "app";
            program = let
              # ビルド時に利用可能なアプリ名を取得
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                =================================
                プロジェクト: Entry POC
                =================================
                
                このプロジェクトで利用可能なコマンド:
                
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
                
                使用例:
                  echo '{"operation": "example"}' | nix run .#run
                  nix run .#test
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          # 実際のアプリケーション
          run = {
            type = "app";
            program = "${pkgs.writeShellScript "run" ''
              echo "Running with input: $(cat)"
            ''}";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "Running tests..."
              echo "All tests passed!"
            ''}";
          };
          
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              echo "Formatting code..."
              echo "Done!"
            ''}";
          };
          
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              echo "Linting code..."
              echo "No issues found!"
            ''}";
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ 
            hello
          ];
        };
      });
}