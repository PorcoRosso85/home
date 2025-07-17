{
  description = "KuzuDB TypeScript/Deno persistence layer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      # システム非依存の出力
      lib = {
        importPath = ./.;
        moduleUrl = "file://${./.}/mod.ts";
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
          ];
          
          shellHook = ''
            echo "KuzuDB TypeScript/Deno persistence layer"
            echo "Deno version: $(deno --version | head -n1)"
          '';
        };
        
        # テストランナー
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test" ''
            cd ${./.}
            ${pkgs.deno}/bin/deno test --allow-read --allow-write --allow-net --allow-env
          ''}/bin/test";
        };
      });
}