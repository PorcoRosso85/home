{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    kuzu-ts.url = "path:../../../persistence/kuzu_ts";
  };

  outputs = { self, nixpkgs, kuzu-ts }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          deno
        ];
        
        shellHook = ''
          echo "KuzuDB TypeScript sample environment"
          echo "Module path: ${kuzu-ts.lib.importPath}"
        '';
      };
      
      apps.${system}.default = {
        type = "app";
        program = "${pkgs.writeShellScriptBin "run" ''
          export KUZU_TS_PATH="${kuzu-ts.lib.importPath}"
          ${pkgs.deno}/bin/deno run --allow-read --allow-write --allow-net --allow-env ${./main_flake.ts}
        ''}/bin/run";
      };
    };
}