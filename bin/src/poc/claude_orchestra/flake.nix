{
  description = "Claude Orchestra - Integration Testing POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            jq
          ];

          shellHook = ''
            echo "Claude Orchestra - Integration Testing POC"
            echo ""
            echo "Commands:"
            echo "  nix run .#test - Run all integration tests"
            echo ""
          '';
        };
        
        apps = {
          # 統合テスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              echo "=== Claude Orchestra Integration Tests ==="
              echo ""
              ${pkgs.deno}/bin/deno test --no-lock --allow-all src/
            ''}";
          };
        };
      });
}