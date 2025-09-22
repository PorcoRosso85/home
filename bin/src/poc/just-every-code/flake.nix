{
  description = "Minimal flake: CDP environment + @just-every/code package";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
      ];
    in {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
        in {
          just-every-code = pkgs.stdenv.mkDerivation {
            pname = "just-every-code";
            version = "0.2.45";

            src = pkgs.fetchurl {
              url = "https://registry.npmjs.org/@just-every/code/-/code-0.2.45.tgz";
              sha256 = "0paifqqvs36jm8w9pv43q3f3wwdqbclkk2200m497c13wn76690l";
            };

            # Node.js runtime dependency
            buildInputs = [ pkgs.nodejs_20 ];

            # No build needed - just copy files
            dontBuild = true;

            installPhase = ''
              runHook preInstall

              mkdir -p $out/bin $out/share/just-every-code

              # Copy all package files
              cp -r * $out/share/just-every-code/

              # Create wrapper script that executes the module directly
              cat > $out/bin/coder << EOF
              #!/bin/bash
              exec ${pkgs.nodejs_20}/bin/node $out/share/just-every-code/bin/coder.js "\$@"
              EOF
              chmod +x $out/bin/coder

              # Create alias to avoid collision with VS Code
              ln -s $out/bin/coder $out/bin/just-every-code

              runHook postInstall
            '';

            # Handle binary name collision with VS Code
            meta = {
              description = "Lightweight coding agent that runs in your terminal";
              homepage = "https://github.com/just-every/code";
              license = pkgs.lib.licenses.asl20;
              mainProgram = "coder"; # Avoid collision with VS Code 'code' command
              maintainers = with pkgs.lib.maintainers; [ ];
            };
          };

          default = self.packages.${system}.just-every-code;
        });

      apps = forAllSystems (system: {
        just-every-code = {
          type = "app";
          program = "${self.packages.${system}.just-every-code}/bin/coder";
        };
        default = self.apps.${system}.just-every-code;
      });

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            # Allow unfree if you want to install google-chrome inside the shell.
            config.allowUnfree = true;
          };
          python = pkgs.python311;
          pythonEnv = python.withPackages (ps: [
            ps.pip
            ps.setuptools
            ps.wheel
            # For the demo script: sync WebSocket client to speak CDP
            ps.websocket-client
          ]);
        in {
          default = pkgs.mkShell {
            packages = [
              # Browser binaries
              pkgs.chromium
              # Uncomment if you prefer proprietary Chrome. Requires allowUnfree=true
              # pkgs.google-chrome

              # Add @just-every/code package
              self.packages.${system}.just-every-code

              # Tooling
              pythonEnv
              pkgs.jq
              pkgs.curl
              pkgs.coreutils
              pkgs.which
            ];

            # Helpful env for predictable profiles & artifacts
            shellHook = ''
              # Use the current working directory as project root (avoids /nix/store when using path:.)
              export JUST_EVERY_CODE_ROOT="$PWD"
              export JUST_EVERY_CODE_PROFILE="$JUST_EVERY_CODE_ROOT/.chromium-profile"
              export JUST_EVERY_CODE_ARTIFACTS="$JUST_EVERY_CODE_ROOT/artifacts"
              mkdir -p "$JUST_EVERY_CODE_PROFILE" "$JUST_EVERY_CODE_ARTIFACTS" || true
              echo "DevShell ready: chromium=$(which chromium || true)"
              echo "Profile: $JUST_EVERY_CODE_PROFILE"
              echo "@just-every/code: $(which coder || echo 'not built yet')"
              echo ""
              echo "Usage:"
              echo "  nix run .#just-every-code  # Run @just-every/code via flake"
              echo "  coder                      # Run directly (after successful build)"
            '';
          };
        }
      );
    };
}
