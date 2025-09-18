{
  description = "SQLite8öhKuzuDB¢ø√¡nPOC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # ≈Åjƒ¸Îí—√±¸∏hWfö©
        packages.default = pkgs.buildEnv {
          name = "kuzu-sqlite-tools";
          paths = with pkgs; [
            sqlite
            kuzu
            bash
          ];
        };

        # ãz∞É
        devShells.default = pkgs.mkShell {
          buildInputs = [ self.packages.${system}.default ];
          
          shellHook = ''
            echo "SQLite + KuzuDB POC∞É"
            echo ")(Ô˝j≥ﬁÛ…:"
            echo "  ./example_attach.sh    - åhjüLã"
            echo "  ./simple_query.sh      - §ÛøÈØ∆£÷Ø®Í"
            echo "  ./batch_query.sh       - –√¡Ø®ÍüL"
            echo "  ./test_integration.sh  - q∆π»üL"
          '';
        };

        # ∆π»üL
        apps.test = {
          type = "app";
          program = "${pkgs.bash}/bin/bash -c '${./test_integration.sh}'";
        };

        # üLã
        apps.example = {
          type = "app";
          program = "${pkgs.bash}/bin/bash -c '${./example_attach.sh}'";
        };
      });
}