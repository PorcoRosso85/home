{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    kuzu-py.url = "path:../../../persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, kuzu-py }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          kuzu-py.packages.${system}.kuzu
        ];
        
        shellHook = ''
          export PYTHONPATH="${kuzu-py.lib.pythonPath}:$PYTHONPATH"
        '';
      };
    };
}