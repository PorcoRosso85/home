{
  description = "EdgarTools - SEC EDGAR data extraction with uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
    ...
  }:
    let
      inherit (nixpkgs) lib;
      
      # Support multiple systems
      forAllSystems = lib.genAttrs [ "x86_64-linux" "aarch64-linux" ];
      
    in {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python312;
          
          # Load uv workspace
          workspace = uv2nix.lib.workspace.loadWorkspace {
            workspaceRoot = ./.;
          };
          
          # Create overlay from workspace
          overlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";  # Prefer binary wheels
          };
          
          # Build fixups for missing metadata in uv.lock
          pyprojectOverrides = _final: _prev: {
            # Add any necessary build fixups here
          };
          
          # Construct Python package set
          pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          }).overrideScope (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
              pyprojectOverrides
            ]
          );
          
        in {
          # Package virtual environment with EdgarTools
          default = pythonSet.mkVirtualEnv "edgartools-env" workspace.deps.default;
          
          # Standalone EdgarTools package
          edgartools = pythonSet.edgartools;
        }
      );
      
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python312;
          
        in {
          # Pure development using uv2nix
          default = self.devShells.${system}.uv2nix;
          
          # Pure uv2nix managed environment
          uv2nix = pkgs.mkShell {
            packages = [
              self.packages.${system}.default
            ];
            
            shellHook = ''
              echo "EdgarTools environment (uv2nix)"
              echo "Python: ${python.version}"
              echo "Testing import..."
              python -c "from edgar import Company; print('✅ EdgarTools ready')" || echo "❌ Import failed"
            '';
          };
          
          # Impure development using uv directly
          impure = pkgs.mkShell {
            packages = [
              python
              pkgs.uv
            ];
            
            env = {
              UV_PYTHON_DOWNLOADS = "never";
              UV_PYTHON = python.interpreter;
            } // lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath pkgs.pythonManylinuxPackages.manylinux1;
            };
            
            shellHook = ''
              unset PYTHONPATH
              echo "EdgarTools environment (impure/uv)"
              echo "Use 'uv pip install edgartools' to install"
            '';
          };
        }
      );
    };
}