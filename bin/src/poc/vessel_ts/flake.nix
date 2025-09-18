{
  description = "TypeScript/Bun Vessel Implementation";

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
            bun
            nodejs_20
            ripgrep
            jq
          ];

          shellHook = ''
            echo "TypeScript/Bun Vessel Development Environment"
            echo "Available commands:"
            echo "  bun test          - Run all tests"
            echo "  bun vessel.ts     - Run basic vessel"
            echo "  bun vessel_data.ts - Run data-aware vessel"
          '';
        };

        packages = {
          test = pkgs.writeShellScriptBin "test" ''
            echo "Running TypeScript/Bun vessel tests..."
            ${pkgs.bun}/bin/bun test
          '';

          demo = pkgs.writeShellScriptBin "demo" ''
            echo "Running TypeScript vessel demo..."
            echo 'console.log("Hello from vessel!")' | ${pkgs.bun}/bin/bun vessel.ts
            echo ""
            echo "Running data-aware vessel demo..."
            echo "test data" | ${pkgs.bun}/bin/bun vessel_data.ts 'console.log("Received:", data)'
          '';
        };
      });
}