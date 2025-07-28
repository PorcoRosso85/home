{
  description = "ASVS Arrow Converter - GitHub to Arrow/Parquet pipeline";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # OWASP ASVS source repository
    asvs-source = {
      url = "github:OWASP/ASVS";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, asvs-source }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        
        pythonPackages = python.pkgs;
        
        # Python dependencies
        pythonDeps = with pythonPackages; [
          pytest
          pytest-cov
          pyarrow     # Arrow形式でのデータ変換用
        ];
        
        # Python environment with all dependencies
        pythonEnv = python.withPackages (ps: pythonDeps);
        
        # ASVS 5.0 data from GitHub
        asvs5Data = pkgs.runCommand "asvs-5.0-data" {} ''
          mkdir -p $out/en
          # Copy markdown files from ASVS repository
          cp -r ${asvs-source}/5.0/en/*.md $out/en/
          echo "ASVS 5.0 data copied to $out"
        '';
        
        # Build Python package
        asvsArrowConverter = pythonPackages.buildPythonPackage {
          pname = "asvs-arrow-converter";
          version = "0.1.0";
          src = self;
          pyproject = true;
          
          build-system = with pythonPackages; [
            setuptools
            wheel
          ];
          
          dependencies = with pythonPackages; [
            pyarrow
          ];
          
          nativeCheckInputs = with pythonPackages; [
            pytest
            pytest-cov
          ];
          
          checkPhase = ''
            pytest test_*.py -v
          '';
          
          pythonImportsCheck = [
            "asvs_arrow_converter"
            "asvs_arrow_types"
          ];
        };
        
        # Python environment with the package
        pythonEnvWithPackage = python.withPackages (ps: [
          asvsArrowConverter
        ] ++ pythonDeps);
        
      in
      {
        packages = {
          default = asvsArrowConverter;
          python-env = pythonEnvWithPackage;
          
          # Test runner
          test = pkgs.writeShellScriptBin "test-asvs-reference" ''
            set -e
            echo "Running ASVS Reference tests..."
            cd ${self}
            export PYTHONPATH="${self}:$PYTHONPATH"
            ${pythonEnvWithPackage}/bin/python -m pytest test_*.py -v
          '';
          
          # Arrow CLI tool
          arrow-cli = pkgs.writeShellScriptBin "asvs-arrow-cli" ''
            set -e
            export PYTHONPATH="${self}:$PYTHONPATH"
            ${pythonEnvWithPackage}/bin/python ${self}/arrow_cli.py "$@"
          '';
          
          # Convert example - uses bundled ASVS 5.0 data
          convert-example = pkgs.writeShellScriptBin "convert-asvs-example" ''
            set -e
            echo "Converting ASVS 5.0 from GitHub to Parquet..."
            
            OUTPUT_DIR="output"
            mkdir -p "$OUTPUT_DIR"
            
            echo "Input: ${asvs5Data}/en"
            echo "Output: $OUTPUT_DIR/asvs_v5.0.parquet"
            
            ${self.packages.${system}.arrow-cli}/bin/asvs-arrow-cli ${asvs5Data}/en -o "$OUTPUT_DIR/asvs_v5.0.parquet" -v
            
            echo ""
            echo "Conversion complete! To read the file:"
            echo "  python example_read_parquet.py $OUTPUT_DIR/asvs_v5.0.parquet"
          '';
          
          # README display
          readme = pkgs.writeShellScriptBin "show-readme" ''
            ${pkgs.less}/bin/less ${self}/README.md
          '';
        };
        
        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/test-asvs-reference";
          };
          
          test = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/test-asvs-reference";
          };
          
          arrow-cli = {
            type = "app";
            program = "${self.packages.${system}.arrow-cli}/bin/asvs-arrow-cli";
          };
          
          convert-example = {
            type = "app";
            program = "${self.packages.${system}.convert-example}/bin/convert-asvs-example";
          };
          
          readme = {
            type = "app";
            program = "${self.packages.${system}.readme}/bin/show-readme";
          };
        };
        
        # Export for other flakes
        lib = {
          inherit asvsArrowConverter asvs5Data;
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnvWithPackage
            # Development tools
            python312Packages.black
            python312Packages.isort
            python312Packages.flake8
            python312Packages.mypy
            python312Packages.ipython
          ];
          
          shellHook = ''
            echo "ASVS Arrow Converter Development Shell"
            echo ""
            echo "Available commands:"
            echo "  nix run .#test              - Run all tests"
            echo "  nix run .#arrow-cli         - Convert ASVS to Parquet"
            echo "  nix run .#convert-example   - Convert bundled ASVS 5.0"
            echo "  nix run .#readme            - Show README"
            echo ""
            echo "Python environment with pytest and pyarrow available"
          '';
        };
      });
}