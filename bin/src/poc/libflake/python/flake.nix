{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    persistence.url = "path:../../../persistence";
  };

  outputs = { self, nixpkgs, persistence }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          python312Packages.kuzu
        ];
        
        shellHook = ''
          export PYTHONPATH="${persistence.lib.pythonPath}:$PYTHONPATH"
        '';
      };
    };
}