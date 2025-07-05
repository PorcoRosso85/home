{
  description = "Symbol Search Implementation with ctags integration (Nushell)"; 

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Nushell版
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
            nushell
            universal-ctags
            search-symbols
          ];

          shellHook = ''
            echo "🔍 Symbol Search Development Environment"
            echo "======================================="
            echo ""
            echo "🦀 Nushell ${pkgs.nushell.version}"
            echo "🏷️  ctags ${pkgs.universal-ctags.version}"
            echo ""
            echo "📋 Available commands:"
            echo "  search-symbols <path>      - Search symbols using ctags"
            echo ""
            echo "🚀 Usage:"
            echo "  nix run . -- <path>        - Search symbols in path"
            echo "  nix run . -- <path> --ext <ext>  - Filter by extension"
            echo ""
          '';
        };

        # 実行可能なアプリケーション
        apps = {
          # デフォルト: search-symbols
          default = {
            type = "app";
            program = "${search-symbols}/bin/search-symbols";
          };

          # シンプルなテスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              echo "Testing search-symbols..."
              
              # Test with Python file
              echo "\nSearching Python files:"
              ${search-symbols}/bin/search-symbols ${./.}/test_data --ext py | 
                ${pkgs.jq}/bin/jq '.symbols | length' | 
                xargs echo "Found symbols:"
              
              # Test with single file
              echo "\nSearching single file:"
              ${search-symbols}/bin/search-symbols ${./.}/test_data/sample.py | 
                ${pkgs.jq}/bin/jq '.metadata.searched_files' | 
                xargs echo "Searched files:"
            ''}"; 
          };

        };

        # パッケージ
        packages.default = search-symbols;
      });
}