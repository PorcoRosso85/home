{
  description = "Qwen-Code CLI tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          # Simple wrapper that uses npx for execution
          qwen-code = pkgs.writeShellScriptBin "qwen-code" ''
            #!${pkgs.bash}/bin/bash
            export PATH="${pkgs.nodejs_20}/bin:$PATH"
            
            # Create a temporary directory for npm cache
            export NPM_CONFIG_CACHE="''${XDG_CACHE_HOME:-$HOME/.cache}/qwen-code-npm"
            mkdir -p "$NPM_CONFIG_CACHE"
            
            # Run qwen-code via npx with caching
            exec ${pkgs.nodejs_20}/bin/npx --yes @qwen-code/qwen-code@latest "$@"
          '';

          default = self.packages.${system}.qwen-code;
        });

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/qwen-code";
        };
      });

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              nodejs_20
              nodePackages.npm
              self.packages.${system}.qwen-code
            ];

            shellHook = ''
              echo "Qwen-Code development shell"
              echo "Node.js: $(node --version)"
              echo "npm: $(npm --version)"
              echo ""
              echo "Run: qwen-code [arguments]"
            '';
          };
        });
    };
}