{
  description = "Code similarity detection tool";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    similarity = {
      url = "github:mizchi/similarity";
      flake = false;
    };
  };
  
  outputs = { self, nixpkgs, flake-utils, similarity }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        apps = {
          # 必須：README表示
          default = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "show-readme" ''
              if [ $# -ne 0 ]; then
                echo "Error: default app does not accept arguments" >&2
                echo "" >&2
              fi
              
              if [ -f ${similarity}/README.md ]; then
                ${pkgs.bat}/bin/bat -p ${similarity}/README.md
              else
                echo "README.md not found"
              fi
            ''}/bin/show-readme";
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            cargo
            rustc
            pkg-config
            openssl
          ];
          shellHook = ''
            echo "Similarity development environment"
            echo "Available commands:"
            echo "  nix run /home/nixos/bin/src/poc/similarity       # Show README"
          '';
        };
      });
}