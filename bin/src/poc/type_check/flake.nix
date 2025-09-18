{
  description = "Type safety comparison across languages following unified conventions";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # 既存のflakeから環境を継承
    python-flake.url = "path:../../flakes/python";
    bun-flake.url = "path:../../flakes/bun";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, bun-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # 各言語の開発環境
        pythonEnv = python-flake.devShells.${system}.default;
        bunEnv = bun-flake.devShells.${system}.default;
        
        # Rust環境
        rustEnv = pkgs.mkShell {
          buildInputs = with pkgs; [
            rustc
            cargo
            rustfmt
            clippy
          ];
        };
        
        # Go環境
        goEnv = pkgs.mkShell {
          buildInputs = with pkgs; [
            go
            gopls
            golangci-lint
          ];
        };
        
        # Zig環境
        zigEnv = pkgs.mkShell {
          buildInputs = with pkgs; [
            zig
            zls
          ];
        };
        
      in
      {
        # 開発シェル
        devShells = {
          default = pkgs.mkShell {
            buildInputs = pythonEnv.buildInputs 
              ++ bunEnv.buildInputs
              ++ rustEnv.buildInputs
              ++ goEnv.buildInputs
              ++ zigEnv.buildInputs
              ++ [ pkgs.just ];
          };
          
          python = pythonEnv;
          typescript = bunEnv;
          go = goEnv;
          rust = rustEnv;
          zig = zigEnv;
        };
        
        # テストコマンド
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "Running type safety tests across all languages..."
              ${pkgs.python312}/bin/python test_flake_structure.py
            ''}";
          };
        };
      });
}