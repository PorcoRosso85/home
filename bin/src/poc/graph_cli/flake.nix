{
  description = "Graph CLI - Display KuzuDB query results in CUI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts-persistence.url = "path:../../persistence/kuzu_ts";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts-persistence }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        graph-cli = pkgs.writeShellScriptBin "graph-cli" ''
          export DENO_DIR="$(mktemp -d)"
          export KUZU_TS_PATH="${kuzu-ts-persistence.lib.importPath}"
          ${pkgs.deno}/bin/deno run \
            --allow-read \
            --allow-write \
            --allow-env \
            --allow-ffi \
            --unstable-ffi \
            --no-lock \
            ${self}/main.ts "$@"
          rm -rf "$DENO_DIR"
        '';
      in
      {
        packages = {
          default = graph-cli;
        };

        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                プロジェクト: graph_cli
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          ui = {
            type = "app";
            program = "${pkgs.writeShellScript "graph-ui" ''
              export DENO_DIR="$(mktemp -d)"
              export KUZU_TS_PATH="${kuzu-ts-persistence.lib.importPath}"
              ${pkgs.deno}/bin/deno run \
                --allow-read \
                --allow-write \
                --allow-env \
                --allow-ffi \
                --unstable-ffi \
                --no-lock \
                ${self}/ui.ts "$@"
              rm -rf "$DENO_DIR"
            ''}";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "テスト未実装"
              exit 0
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              if [ -f "${self}/README.md" ]; then
                cat "${self}/README.md"
              else
                echo "README.md not found"
              fi
            ''}";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
          ];
          
          shellHook = ''
            export KUZU_TS_PATH="${kuzu-ts-persistence.lib.importPath}"
            echo "Graph CLI development environment"
            echo "Run 'deno task dev' to start development"
          '';
        };
      });
}