{
  description = "Codex CLI flake (shell wrapper, no nix run/direnv)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";

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
        let pkgs = import nixpkgs { inherit system; }; in
        rec {
          # Shell app wrapper around `npx @openai/codex` with Node.js 22
          codex = pkgs.writeShellApplication {
            name = "codex";
            runtimeInputs = [ pkgs.nodejs_22 ];
            text = ''
              exec npx --yes @openai/codex --dangerously-bypass-approvals-and-sandbox "$@"
            '';
          };
          default = codex;
        }
      );

      # devShells intentionally omitted (flake package only)
    };
}
