{
  description = "ctags-based path finder";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        path-by-ctags = pkgs.python3.pkgs.buildPythonApplication {
          pname = "path-by-ctags";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pkgs; [
            universal-ctags
          ];
          
          installPhase = ''
            mkdir -p $out/bin
            cp path_by_ctags.py $out/bin/path-by-ctags
            chmod +x $out/bin/path-by-ctags
          '';
        };
      in
      {
        packages.default = path-by-ctags;
        
        apps.default = flake-utils.lib.mkApp {
          drv = path-by-ctags;
          exePath = "/bin/path-by-ctags";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            universal-ctags
          ];
        };
      });
}