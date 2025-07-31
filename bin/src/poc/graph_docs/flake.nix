{
  description = "graph_docs POC - Dual KuzuDB Query Interface";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py-flake.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
    tags-in-dir.url = "path:/home/nixos/bin/src/poc/tags_in_dir";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py-flake, tags-in-dir, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Build graph_docs as a proper Python package
        graphDocsPackage = pkgs.python312Packages.buildPythonPackage rec {
          pname = "graph_docs";
          version = "0.1.0";
          src = ./.;
          
          pyproject = true;
          
          build-system = with pkgs.python312Packages; [
            setuptools
            wheel
          ];
          
          propagatedBuildInputs = with pkgs.python312Packages; [
            kuzu
          ];
          
          nativeCheckInputs = with pkgs.python312Packages; [
            pytest
            pytest-asyncio
          ];
          
          pythonImportsCheck = [ "graph_docs" ];
          
          # Disable tests during build (run separately)
          doCheck = false;
        };
        
        # Python environment with our package and test dependencies
        pythonEnv = pkgs.python312.withPackages (ps: [
          graphDocsPackage
          ps.pytest
          ps.pytest-asyncio
        ]);

      in
      {
        packages = {
          default = graphDocsPackage;
          pythonEnv = pythonEnv;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ 
            pythonEnv 
            pkgs.pyright
            pkgs.ruff
          ];
          
          shellHook = ''
            echo "graph_docs development environment"
            echo "Python package: graph_docs"
            echo "CLI: graph-docs"
            echo ""
            echo "Available commands:"
            echo "  graph-docs query DB1 DB2 'MATCH (n) RETURN n LIMIT 5'"
            echo "  graph-docs info DB1 DB2"
            echo "  graph-docs parallel DB1 DB2 'QUERY1' 'QUERY2'"
            echo ""
            echo "Development tools:"
            echo "  pytest - Run tests"
            echo "  pyright - Type checker"
            echo "  ruff - Linter"
          '';
        };

        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                プロジェクト: graph_docs POC
                
                責務: 2つのKuzuDBディレクトリに対する同時クエリとリレーション定義
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${./.}
              export PYTHONPATH="${./.}:$PYTHONPATH"
              exec ${pythonEnv}/bin/pytest -v
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };

          query = {
            type = "app";
            program = "${pythonEnv}/bin/graph-docs";
          };


        };
      }
    );
}