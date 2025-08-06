{
  description = "Bash development environment";

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
            # Bash,S
            bash
            
            # LSP
            nodePackages.bash-language-server
            
            # YÑ„ê
            shellcheck
            
            # ∆π»’Ï¸‡Ô¸Ø
            bats
            
            # ’©¸ﬁ√ø¸
            shfmt
          ];

          shellHook = ''
            echo "Bash development environment loaded"
            echo "Available tools:"
            echo "  - bash-language-server: LSP for Bash"
            echo "  - shellcheck: Static analysis tool"
            echo "  - bats: Bash Automated Testing System"
            echo "  - shfmt: Bash formatter"
          '';
        };
      });
}