{
  description = "ctags-based code analysis library with KuzuDB persistence";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake }:
    let
      # Define overlay for library usage
      overlay = final: prev: {
        pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
          (python-final: python-prev: {
            tags-in-dir = python-final.buildPythonPackage rec {
              pname = "tags-in-dir";
              version = "0.1.0";
              src = ./.;
              
              propagatedBuildInputs = with python-final; [
                kuzu
              ];
              
              buildInputs = with python-final; [
                pytest
              ];
              
              # No setup.py, so we need to manually install
              format = "other";
              
              installPhase = ''
                mkdir -p $out/${python-final.python.sitePackages}/tags_in_dir
                cp tags_in_dir.py $out/${python-final.python.sitePackages}/tags_in_dir/__init__.py
                cp kuzu_storage.py $out/${python-final.python.sitePackages}/tags_in_dir/
                cp call_detector.py $out/${python-final.python.sitePackages}/tags_in_dir/
                cp analysis_queries.py $out/${python-final.python.sitePackages}/tags_in_dir/
              '';
              
              pythonImportsCheck = [ "tags_in_dir" ];
              
              meta = with prev.lib; {
                description = "ctags-based code analysis library with KuzuDB persistence";
                license = licenses.mit;
              };
            };
          })
        ];
      };
    in
    {
      # Export the overlay at the top level (not per-system)
      overlays.default = overlay;
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        # Apply our overlay to get the extended Python packages
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];
        };
        
        # Get Python environment from parent flake
        pythonBase = python-flake.packages.${system}.pythonEnv;
        
        # Create Python environment with our package and test dependencies
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          tags-in-dir
          pytest
          kuzu
        ]);
        
      in
      {
        
        # Provide the Python environment as the main output
        packages = {
          default = pythonEnv;  # Python environment with the library installed
        };
        
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.universal-ctags
            pkgs.ruff
            pkgs.black
            pkgs.mypy
          ];
          
          shellHook = ''
            echo "tags_in_dir development environment"
            echo "Library is available as Python package: tags_in_dir"
            echo ""
            echo "Python usage:"
            echo "  from tags_in_dir import CtagsParser, Symbol"
            echo "  from tags_in_dir.kuzu_storage import KuzuStorage"
            echo "  from tags_in_dir.call_detector import CallDetector"
            echo ""
            echo "Available tools:"
            echo "  ctags - Universal Ctags for code analysis"
            echo "  python - Python with tags_in_dir library"
            echo "  pytest - Run tests"
            echo "  ruff/black - Python formatting"
            echo "  mypy - Type checker"
          '';
        };
        
        # Applications
        apps = rec {
          # Default app shows available commands
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                tags_in_dir: ctags-based code analysis library
                
                詳細な使用方法はREADMEを参照してください：
                  nix run .#readme
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
                
                基本的な使い方:
                  find -d 3 | nix run .#generate
                  nix run .#generate /path/to/project --export-dir ./output
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              # Run in source directory
              cd ${./.}
              export PATH="${pkgs.universal-ctags}/bin:$PATH"
              export PYTHONPATH="${pythonEnv}/${pythonEnv.python.sitePackages}:$PYTHONPATH"
              exec ${pythonEnv}/bin/pytest -v "$@"
            ''}";
          };
          
          # Show README
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };
          
          # Format code
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              cd ${./.}
              ${pkgs.black}/bin/black *.py
              ${pkgs.ruff}/bin/ruff format *.py
            ''}";
          };
          
          # Lint code
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              cd ${./.}
              ${pkgs.ruff}/bin/ruff check *.py
            ''}";
          };
          
          # Type check
          typecheck = {
            type = "app";
            program = "${pkgs.writeShellScript "typecheck" ''
              cd ${./.}
              ${pkgs.mypy}/bin/mypy *.py
            ''}";
          };
          
          # Example usage demonstration
          example = {
            type = "app";
            program = "${pkgs.writeShellScript "example" ''
              ${pythonEnv}/bin/python ${./example_integration.py}
            ''}";
          };
          
          # Generate command for processing URIs
          generate = {
            type = "app";
            program = "${pkgs.writeShellScript "generate" ''
              export PATH="${pkgs.universal-ctags}/bin:$PATH"
              exec ${pythonEnv}/bin/python ${./cli.py} "$@"
            ''}";
          };
        };
      });
}