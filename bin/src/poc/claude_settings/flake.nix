{
  description = "Claude Settings Dynamic Permission Control POC";

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
            git
          ];

          shellHook = ''
            echo "Claude Settings POC - Dynamic Permission Control"
            echo ""
            echo "Commands:"
            echo "  deno test              - Run all tests"
            echo "  deno test --filter=permission - Run permission tests"
            echo "  deno test --filter=hook      - Run hook tests"
            echo "  nix run .#test-red     - Run TDD Red phase tests"
            echo ""
          '';
        };
        
        apps.test-red = {
          type = "app";
          program = "${pkgs.writeShellScript "run-red-tests" ''
            cd ${./.}
            echo "=== TDD Red Phase: Settings.json Permission Control ==="
            echo ""
            ${pkgs.deno}/bin/deno test --allow-all --filter="permission" || echo "Expected failures ✓"
            echo ""
            echo "=== TDD Red Phase: Hook Execution Verification ==="
            echo ""
            ${pkgs.deno}/bin/deno test --allow-all --filter="hook" || echo "Expected failures ✓"
          ''}";
        };
        
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "run-all-tests" ''
            cd ${./.}
            ${pkgs.deno}/bin/deno test --allow-all "$@"
          ''}";
        };
      });
}