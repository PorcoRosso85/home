{
  description = "Symbol Search Implementation with ctags integration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python環境の定義
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          # テスト用
          pytest
          pytest-cov
          # 型チェック用
          mypy
          types-toml
          # フォーマッター
          black
          # リンター  
          ruff
        ]);

        # Python版 (legacy - will be removed)
        search-symbols-py = pkgs.writeScriptBin "search-symbols-py" ''
          #!${pythonEnv}/bin/python
          ${builtins.readFile ./search_standalone.py}
        '';
        
        # Nushell版 (new implementation)
        nuScript = pkgs.writeTextFile {
          name = "search_symbols.nu";
          text = builtins.readFile ./search_symbols.nu;
          executable = false;
        };
        
        search-symbols = pkgs.writeShellScriptBin "search-symbols" ''
          export PATH="${pkgs.lib.makeBinPath [pkgs.universal-ctags]}:$PATH"
          exec ${pkgs.nushell}/bin/nu ${nuScript} "$@"
        '';
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            nushell
            universal-ctags
            search-symbols
            search-symbols-py
          ];

          shellHook = ''
            echo "🔍 Symbol Search Development Environment"
            echo "======================================="
            echo ""
            echo "🐍 Python ${pkgs.python311.version}"
            echo "🦀 Nushell ${pkgs.nushell.version}"
            echo "🏷️  ctags ${pkgs.universal-ctags.version}"
            echo ""
            echo "📋 Available commands:"
            echo "  search-symbols <path>      - Search symbols (Nushell)"
            echo "  search-symbols-py <path>   - Search symbols (Python)"
            echo ""
            echo "🚀 Usage:"
            echo "  nix run . -- <path>        - Run Nushell version"
            echo "  nix run .#python -- <path> - Run Python version"
            echo "  nix run .#test             - Run tests"
            echo ""
          '';
        };

        # 実行可能なアプリケーション
        apps = {
          # デフォルト: search-symbols (Nushell版)
          default = {
            type = "app";
            program = "${search-symbols}/bin/search-symbols";
          };
          
          # Python版 (レガシー)
          python = {
            type = "app";
            program = "${search-symbols-py}/bin/search-symbols-py";
          };

          # テスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export TMPDIR=$(mktemp -d)
              cd $TMPDIR
              
              # Copy test files
              cp -r ${./.}/test_data .
              cp ${./.}/test_standalone.py .
              cp ${./.}/search_standalone.py .
              
              echo "Running tests..."
              ${pythonEnv}/bin/python test_standalone.py
              
              # Cleanup (ignore errors)
              rm -rf $TMPDIR 2>/dev/null || true
            ''}";
          };

          # コードフォーマット
          format = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              echo "Formatting Python files..."
              ${pythonEnv}/bin/black ${./.}/*.py
            ''}";
          };

          # リント
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              echo "Linting Python files..."
              ${pythonEnv}/bin/ruff check ${./.}/*.py
            ''}";
          };

          # 型チェック
          typecheck = {
            type = "app";
            program = "${pkgs.writeShellScript "typecheck" ''
              echo "Type checking..."
              ${pythonEnv}/bin/mypy ${./.}/types.py ${./.}/search.py --strict
            ''}";
          };
        };

        # パッケージ
        packages.default = search-symbols;
      });
}