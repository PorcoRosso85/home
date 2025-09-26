{
  description = "Codex CLI flake using nixpkgs codex package with nix run support";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs, ... }:
    let
      inherit (nixpkgs.lib) genAttrs;
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
    in {
      packages = genAttrs systems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in rec {
          codex = pkgs.codex;
          default = codex;
        }
      );

      apps = genAttrs systems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          codexApp = {
            type = "app";
            program = "${pkgs.codex}/bin/codex";
          };
        in {
          default = codexApp;
          codex = codexApp;
        }
      );

      # devShells intentionally omitted (flake package only)
    };
}
