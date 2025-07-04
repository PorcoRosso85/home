{
  description = "E2E Testing with Playwright";

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
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_20
            nodePackages.npm
            
            # Playwright dependencies
            chromium
            # Playwright needs these system libraries
            xorg.libX11
            xorg.libXcomposite
            xorg.libXcursor
            xorg.libXdamage
            xorg.libXext
            xorg.libXfixes
            xorg.libXi
            xorg.libXrender
            xorg.libXtst
            xorg.libxkbfile
            nss
            nspr
            alsa-lib
            cups
            expat
            libuuid
          ];

          shellHook = ''
            echo "🎭 Playwright E2E Test Environment"
            echo "==================================="
            echo ""
            echo "📋 Setup commands:"
            echo "  npm install          - Install Playwright"
            echo "  npm run test:setup   - Verify Playwright installation"
            echo "  npm test            - Run E2E tests"
            echo ""
            echo "🌐 Browser:"
            echo "  - Chromium ${pkgs.chromium.version}"
            echo ""
            
            # Set Playwright to use system browsers
            export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
            export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=${pkgs.chromium}/bin/chromium
          '';
        };
      });
}