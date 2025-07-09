{
  description = "Event Log Persistence for Causal Ordering POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        testScript = pkgs.writeShellScriptBin "test" ''
          echo "[STORE_LOG] 🗄️ Event Log Persistence Test Environment"
          echo "[STORE_LOG] Running tests..."
          ${pkgs.deno}/bin/deno test \
            --allow-read \
            --allow-write \
            --allow-env \
            --allow-net \
            event-log-persistence.test.ts
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
          ];
          
          shellHook = ''
            echo "[STORE_LOG] 🗄️ Event Log Persistence Development Environment"
            echo "[STORE_LOG] Run tests with: nix run .#test"
          '';
        };
        
        apps.test = flake-utils.lib.mkApp {
          drv = testScript;
        };
      });
}