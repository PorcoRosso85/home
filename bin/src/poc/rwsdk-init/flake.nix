{
  description = "React/SSR routing transition diagram POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-readme.url = "path:../flake-readme";
  };

  outputs = inputs@{ flake-parts, flake-readme, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        flake-readme.flakeModules.readme
      ];
      
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      
      perSystem = { config, self', inputs', pkgs, system, ... }: {
        # Enable readme.nix validation
        readme.enable = true;
        
        # Development shell for React/TypeScript development
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_22
          ];
          
          shellHook = ''
            echo "🚀 React transition diagram POC environment"
            echo "Node.js: $(node --version)"
            echo "npm: $(npm --version)"
            echo ""
            echo "Next steps:"
            echo "1. npm install"
            echo "2. npm run dev"
            echo "3. nix run .#dev-worker-remote (for remote development)"
            echo "4. nix run .#test"
          '';
        };

        apps = {
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo" ''
              cd ${./.}
              ${pkgs.nodejs_22}/bin/npm run build
              echo "Starting demo server..."
              ${pkgs.nodejs_22}/bin/npx serve dist -s
            ''}";
          };
          
          dev = {
            type = "app";
            program = "${pkgs.writeShellScript "dev" ''
              cd ${./.}
              ${pkgs.nodejs_22}/bin/npm run dev
            ''}";
          };

          dev-worker = {
            type = "app";
            program = "${pkgs.writeShellScript "dev-worker" ''
              cd ${./.}
              ${pkgs.nodejs_22}/bin/npm run dev:worker
            ''}";
          };

          dev-worker-remote = {
            type = "app";
            program = "${pkgs.writeShellScript "dev-worker-remote" ''
              cd ${./.}
              ${pkgs.nodejs_22}/bin/npx wrangler dev --remote
            ''}";
          };

          deploy = {
            type = "app";
            program = "${pkgs.writeShellScript "deploy" ''
              cd ${./.}
              ${pkgs.nodejs_22}/bin/npm run deploy
            ''}";
          };

          deploy-worker = {
            type = "app";
            program = "${pkgs.writeShellScript "deploy-worker" ''
              cd ${./.}
              ${pkgs.nodejs_22}/bin/npm run deploy:worker
            ''}";
          };

          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${./.}
              ${pkgs.nodejs_22}/bin/npm test
            ''}";
          };
        };
      };
    };
}
