{
  description = "POC: Multiple URI Site Management System";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python311Packages;
        
        # Development dependencies
        devDependencies = with pythonPackages; [
          pytest
          black
          mypy
          requests
          beautifulsoup4
          pydantic
          httpx
        ];
      in
      {
        # Main package (POC implementation)
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "multi-uri-site-manager";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pkgs.python311 ] ++ devDependencies;
          
          installPhase = ''
            mkdir -p $out/bin
            cp -r . $out/src
            
            # Create executable wrapper
            cat > $out/bin/multi-uri-site-manager << 'EOF'
            #!/usr/bin/env python3
            import sys
            sys.path.insert(0, "${placeholder "out"}/src")
            from main import main
            main()
            EOF
            
            chmod +x $out/bin/multi-uri-site-manager
          '';
        };

        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [ pkgs.python311 ] ++ devDependencies;
          
          shellHook = ''
            echo "Multiple URI Site Management POC Development Environment"
            echo "Run 'nix run .' to see available commands"
          '';
        };

        # Applications
        apps = rec {
          # Default app - show available commands
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                ×í¸§¯È: Multiple URI Site Management POC
                
                ‚: pURIkKK‹µ¤È¡’¹‡Y‹‚õŸ<
                
                )(ïıj³ŞóÉ:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          # Run tests
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${self.packages.${system}.default.src}
              exec ${pythonPackages.pytest}/bin/pytest -v tests/
            ''}";
          };
          
          # Show README
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };
          
          # Run the main application
          run = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/multi-uri-site-manager";
          };
          
          # Format code
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              ${pythonPackages.black}/bin/black .
            ''}";
          };
          
          # Type check
          typecheck = {
            type = "app";
            program = "${pkgs.writeShellScript "typecheck" ''
              ${pythonPackages.mypy}/bin/mypy .
            ''}";
          };
        };
      });
}