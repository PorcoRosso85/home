{
  description = "Self-documenting Elixir app";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        elixir = pkgs.beam.packages.erlangR26.elixir_1_15;
        
        app = pkgs.writeShellScriptBin "analyzer" ''
          ${elixir}/bin/elixir ${./analyzer.exs} "$@"
        '';
      in
      {
        packages = {
          default = app;
          analyzer = app;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ elixir ];
        };
      });
}