{
  description = "Claude Graph POC - KuzuDBによる自律的タスク探索・計画";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        projectDir = "/home/nixos/bin/src/poc/claude_graph";
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            python311
            nodePackages.typescript
            nodePackages.typescript-language-server
            nodePackages.prettier
            dprint
          ];
        };
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${projectDir}
              ${pkgs.deno}/bin/deno test taskExplorer.test.ts taskPlanner.test.ts versionBasedExplorer.test.ts --allow-read --no-check
            ''}";
          };
          
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              cd ${projectDir}
              ${pkgs.deno}/bin/deno fmt *.ts
            ''}";
          };
        };
      });
}