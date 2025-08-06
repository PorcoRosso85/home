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
          default = pkgs.buildNpmPackage {
            pname = "qwen-code";
            version = "latest";

            src = pkgs.fetchFromGitHub {
              owner = "QwenLM";
              repo = "qwen-code";
              rev = "main";
              hash = "sha256-YKnGUCoK6sV3KwGh5G/to+dYrssxky2rcoPQAAeqGkA=";
            };

            npmDepsHash = "sha256-YKnGUCoK6sV3KwGh5G/to+dYrssxky2rcoPQAAeqGkA=";

            nodejs = pkgs.nodejs_20;

            installPhase = ''
              mkdir -p $out/bin
              npm pack
              npm install -g *.tgz --prefix=$out
            '';
          };
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
            ];
          };
        });
    };
}