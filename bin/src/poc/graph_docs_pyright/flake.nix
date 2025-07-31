{
  description = "graph_docs_pyright - Pyright-based code analysis with KuzuDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
    log-py.url = "path:/home/nixos/bin/src/telemetry/log_py";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py, log-py, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Get packages from flake inputs
        pythonFlakePackages = python-flake.packages.${system};
        kuzuPyPackage = kuzu-py.packages.${system}.default;
        logPyPackage = log-py.packages.${system}.default;
        
        # Build graph_docs_pyright as a proper Python package
        graphDocsPyrightPackage = pkgs.python312Packages.buildPythonPackage rec {
          pname = "graph_docs_pyright";
          version = "0.1.0";
          src = ./.;
          
          pyproject = true;
          
          build-system = with pkgs.python312Packages; [
            setuptools
            wheel
          ];
          
          propagatedBuildInputs = with pkgs.python312Packages; [
            kuzuPyPackage
            logPyPackage
            # Pyright LSP client dependencies
            pygls
            lsprotocol
            aiofiles
          ];
          
          nativeCheckInputs = with pkgs.python312Packages; [
            pytest
            pytest-asyncio
            pytest-timeout
          ];
          
          pythonImportsCheck = [ "graph_docs" ];
          
          # Disable tests during build (run separately)
          doCheck = false;
        };
        
        # Python environment with our package and test dependencies
        pythonEnv = pkgs.python312.withPackages (ps: [
          graphDocsPyrightPackage
          ps.pytest
          ps.pytest-asyncio
          ps.pytest-timeout
          # Additional development dependencies
          ps.ipython
          ps.rich
        ]);

      in
      {
        packages = {
          default = graphDocsPyrightPackage;
          pythonEnv = pythonEnv;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ 
            pythonEnv 
            pythonFlakePackages.pyright
            pythonFlakePackages.ruff
            pkgs.nodejs  # Required for pyright server
          ];
          
          shellHook = ''
            echo "graph_docs_pyright development environment"
            echo "Pyright-based code analysis with KuzuDB"
            echo ""
            echo "Available tools:"
            echo "  pyright - Type checker and language server"
            echo "  pytest - Run tests"
            echo "  ruff - Linter"
            echo "  ipython - Interactive Python shell"
            echo ""
            echo "Development workflow:"
            echo "  1. nix develop - Enter development environment"
            echo "  2. pytest -v - Run tests"
            echo "  3. pyright - Check types"
            echo ""
            echo "Next steps:"
            echo "  - Implement Pyright LSP client"
            echo "  - Extend KuzuDB schema for type information"
            echo "  - Create analysis queries"
          '';
        };

        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                ������: graph_docs_pyright
                
                ��: Pyright�(W_��X����hKuzuDBk��8�
                
                )(��j����:
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
              export PATH="${pythonFlakePackages.pyright}/bin:$PATH"
              echo "Running minimal test..."
              ${pythonEnv}/bin/python test_minimal.py
              echo -e "\nRunning persistence tests..."
              ${pythonEnv}/bin/python test_persistence.py
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };

          analyze = {
            type = "app";
            program = "${pkgs.writeShellScript "analyze" ''
              echo "Pyright analyzer is not yet implemented"
              echo "This will analyze a project using Pyright LSP and store results in KuzuDB"
              exit 1
            ''}";
          };
        };
      }
    );
}