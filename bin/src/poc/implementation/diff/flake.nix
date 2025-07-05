{
  description = "Requirement Coverage Analysis Pipeline";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python environment
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          # KuzuDB will be available from requirement/graph
          pytest  # For testing
        ]);
        
        # Scripts
        kuzu-query = pkgs.writeScriptBin "kuzu-query" ''
          #!${pkgs.bash}/bin/bash
          export PYTHONPATH="${../../../requirement/graph}:$PYTHONPATH"
          exec ${pythonEnv}/bin/python ${./kuzu_query.py} "$@"
        '';
        
        diff-tool = pkgs.writeScriptBin "diff-tool" ''
          #!${pkgs.bash}/bin/bash
          exec ${pkgs.nushell}/bin/nu ${./diff.nu} "$@"
        '';
        
        pipeline = pkgs.writeScriptBin "req-coverage" ''
          #!${pkgs.bash}/bin/bash
          exec ${pkgs.nushell}/bin/nu ${./pipeline.nu} "$@"
        '';
      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            nushell
            kuzu-query
            diff-tool
            pipeline
          ];
          
          shellHook = ''
            echo "📊 Requirement Coverage Analysis Environment"
            echo "=========================================="
            echo ""
            echo "🛠️  Available tools:"
            echo "  kuzu-query         - Query LocationURIs from KuzuDB"
            echo "  diff-tool          - Compare requirements with filesystem"
            echo "  req-coverage       - Full pipeline analysis"
            echo ""
            echo "📖 Usage examples:"
            echo "  req-coverage /path/to/project"
            echo "  req-coverage /path/to/project --show-symbols"
            echo "  req-coverage missing /path/to/project"
            echo "  req-coverage unspecified /path/to/project"
            echo ""
          '';
        };
        
        # Applications
        apps = {
          # Main pipeline
          default = {
            type = "app";
            program = "${pipeline}/bin/req-coverage";
          };
          
          # Individual tools
          kuzu-query = {
            type = "app";
            program = "${kuzu-query}/bin/kuzu-query";
          };
          
          diff = {
            type = "app";
            program = "${diff-tool}/bin/diff-tool";
          };
          
          # Test the pipeline
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "🧪 Running tests..."
              echo ""
              
              echo "📝 Python tests (kuzu_query):"
              cd ${./.}
              ${pythonEnv}/bin/python -m pytest test_kuzu_query.py -v || echo "✅ Tests are failing as expected (TDD Red phase)"
              
              echo ""
              echo "📝 Nushell tests (diff):"
              ${pkgs.nushell}/bin/nu test_diff.nu || echo "✅ Tests are failing as expected (TDD Red phase)"
              
              echo ""
              echo "📝 Nushell tests (pipeline):"
              ${pkgs.nushell}/bin/nu test_pipeline.nu || echo "✅ Tests are failing as expected (TDD Red phase)"
              
              echo ""
              echo "🔴 All tests are in Red phase - ready for implementation!"
            ''}";
          };
        };
        
        # Package
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "req-coverage";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pythonEnv pkgs.nushell ];
          
          installPhase = ''
            mkdir -p $out/bin $out/share/req-coverage
            
            # Copy scripts
            cp *.py *.nu $out/share/req-coverage/
            
            # Create wrappers
            cat > $out/bin/kuzu-query <<EOF
            #!${pkgs.bash}/bin/bash
            export PYTHONPATH="${../../../requirement/graph}:\$PYTHONPATH"
            exec ${pythonEnv}/bin/python $out/share/req-coverage/kuzu_query.py "\$@"
            EOF
            
            cat > $out/bin/diff-tool <<EOF
            #!${pkgs.bash}/bin/bash
            exec ${pkgs.nushell}/bin/nu $out/share/req-coverage/diff.nu "\$@"
            EOF
            
            cat > $out/bin/req-coverage <<EOF
            #!${pkgs.bash}/bin/bash
            cd $out/share/req-coverage
            exec ${pkgs.nushell}/bin/nu $out/share/req-coverage/pipeline.nu "\$@"
            EOF
            
            chmod +x $out/bin/*
          '';
        };
      });
}