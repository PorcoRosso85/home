{
  description = "ctags-based code analysis tool with KuzuDB persistence";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Inherit Python environment from parent flake and extend it
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pytest
          kuzu
        ]);
        
        # Package definition for tags_in_dir (placeholder)
        tagsInDirPackage = pkgs.writeScriptBin "tags-in-dir" ''
          #!${pythonEnv}/bin/python
          print("tags_in_dir - ctags-based code analysis with KuzuDB")
          print("Implementation pending...")
        '';
      in
      {
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
            echo "Available commands:"
            echo "  ctags - Universal Ctags for code analysis"
            echo "  python - Python with kuzu and pytest"
            echo "  pytest - Run tests"
            echo "  ruff - Python linter"
            echo "  black - Python formatter"
            echo "  mypy - Python type checker"
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
                tags_in_dir: ctags-based code analysis with KuzuDB
                
                Available commands:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          # Main application
          tags-in-dir = {
            type = "app";
            program = "${tagsInDirPackage}/bin/tags-in-dir";
          };
          
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              # Run in source directory
              cd ${./.}
              export PATH="${pkgs.universal-ctags}/bin:$PATH"
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
        };
        
        # Package export
        packages.default = tagsInDirPackage;
      });
}