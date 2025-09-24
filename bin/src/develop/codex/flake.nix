{
  description = "Codex CLI flake (shell wrapper, no nix run/direnv)";

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
        in {
          default = {
            type = "app";
            program = "${pkgs.codex}/bin/codex";
          };
        }
      );

      # devShells intentionally omitted (flake package only)
    };
}
