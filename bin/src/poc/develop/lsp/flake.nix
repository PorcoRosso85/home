{
  description = "LSMCP with improved Python CLI support";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python環境の設定
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          python-lsp-server
          pylsp-mypy
          python-lsp-ruff
          pyflakes
          pycodestyle
          pydocstyle
          autopep8
          yapf
        ]);

        # 改良版Python診断ツール
        pythonDiagnostics = pkgs.writeShellScriptBin "python-diagnostics" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          # カラー定義
          if [[ -t 1 ]]; then
            RED='\033[0;31m'
            GREEN='\033[0;32m'
            YELLOW='\033[0;33m'
            BLUE='\033[0;34m'
            BOLD='\033[1m'
            NC='\033[0m' # No Color
          else
            RED=""
            GREEN=""
            YELLOW=""
            BLUE=""
            BOLD=""
            NC=""
          fi
          
          # デフォルト値
          CHECK_TYPE="all"
          FORMAT="human"
          SUMMARY_ONLY=false
          FILES=()
          
          # ヘルプ表示
          show_help() {
            cat << EOF
          Python Diagnostics Tool
          
          Usage: python-diagnostics [OPTIONS] <file.py> [file2.py ...]
          
          Options:
            --check=TYPE    Run specific check only (syntax|type|lint|style|security|all)
            --format=FMT    Output format (human|json|github)
            --summary       Show summary only
            -h, --help      Show this help message
          
          Examples:
            python-diagnostics main.py
            python-diagnostics --check=type src/*.py
            python-diagnostics --format=json main.py
          EOF
          }
          
          # 引数解析
          while [[ $# -gt 0 ]]; do
            case $1 in
              --check=*)
                CHECK_TYPE="''${1#*=}"
                shift
                ;;
              --format=*)
                FORMAT="''${1#*=}"
                shift
                ;;
              --summary)
                SUMMARY_ONLY=true
                shift
                ;;
              -h|--help)
                show_help
                exit 0
                ;;
              -*)
                echo "Unknown option: $1"
                show_help
                exit 2
                ;;
              *)
                FILES+=("$1")
                shift
                ;;
            esac
          done
          
          # ファイルが指定されていない場合
          if [[ ''${#FILES[@]} -eq 0 ]]; then
            echo "Error: No files specified"
            show_help
            exit 2
          fi
          
          # 結果を格納する変数
          TOTAL_ERRORS=0
          TOTAL_WARNINGS=0
          FILES_WITH_ISSUES=0
          
          # JSON出力の準備
          if [[ "$FORMAT" == "json" ]]; then
            echo "{"
            echo '  "files": ['
          fi
          
          # ヘッダー表示（human形式）
          if [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
            echo -e "''${BOLD}Python Diagnostics Report''${NC}"
            echo "========================"
            echo ""
            echo "Checking ''${#FILES[@]} file(s)..."
            echo ""
          fi
          
          # 各ファイルをチェック
          for i in "''${!FILES[@]}"; do
            FILE="''${FILES[$i]}"
            FILE_ERRORS=0
            FILE_WARNINGS=0
            
            if [[ ! -f "$FILE" ]]; then
              echo -e "''${RED}✗ Error: File not found: $FILE''${NC}" >&2
              continue
            fi
            
            # 各チェックの実行
            if [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
              echo -e "''${BLUE}Checking $FILE...''${NC}"
            fi
            
            # 構文チェック
            if [[ "$CHECK_TYPE" == "all" ]] || [[ "$CHECK_TYPE" == "syntax" ]]; then
              if ! ${pythonEnv}/bin/python -m py_compile "$FILE" 2>/dev/null; then
                ((FILE_ERRORS++))
                if [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
                  echo -e "  ''${RED}✗ Syntax Error''${NC}"
                fi
              fi
            fi
            
            # 型チェック
            if [[ "$CHECK_TYPE" == "all" ]] || [[ "$CHECK_TYPE" == "type" ]]; then
              MYPY_OUTPUT=$(${pkgs.python3Packages.mypy}/bin/mypy --no-error-summary "$FILE" 2>&1 || true)
              if echo "$MYPY_OUTPUT" | grep -q "error:"; then
                MYPY_ERRORS=$(echo "$MYPY_OUTPUT" | grep -c "error:" || true)
                ((FILE_ERRORS+=MYPY_ERRORS))
                if [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
                  echo -e "  ''${RED}✗ Type errors: $MYPY_ERRORS''${NC}"
                fi
              elif [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
                echo -e "  ''${GREEN}✓ Type check passed''${NC}"
              fi
            fi
            
            # Linting (ruff)
            if [[ "$CHECK_TYPE" == "all" ]] || [[ "$CHECK_TYPE" == "lint" ]]; then
              if ! ${pkgs.ruff}/bin/ruff check "$FILE" > /dev/null 2>&1; then
                RUFF_OUTPUT=$(${pkgs.ruff}/bin/ruff check "$FILE" 2>&1 || true)
                RUFF_COUNT=$(echo "$RUFF_OUTPUT" | grep -cE "^$FILE:" || true)
                ((FILE_WARNINGS+=RUFF_COUNT))
                if [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
                  echo -e "  ''${YELLOW}⚠ Linting issues: $RUFF_COUNT''${NC}"
                fi
              elif [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
                echo -e "  ''${GREEN}✓ Linting passed''${NC}"
              fi
            fi
            
            # 結果の集計
            if [[ $FILE_ERRORS -gt 0 ]] || [[ $FILE_WARNINGS -gt 0 ]]; then
              ((FILES_WITH_ISSUES++))
            fi
            ((TOTAL_ERRORS+=FILE_ERRORS))
            ((TOTAL_WARNINGS+=FILE_WARNINGS))
            
            # ファイルごとの結果表示
            if [[ "$FORMAT" == "human" ]] && [[ "$SUMMARY_ONLY" == "false" ]]; then
              if [[ $FILE_ERRORS -eq 0 ]] && [[ $FILE_WARNINGS -eq 0 ]]; then
                echo -e "  ''${GREEN}✓ No issues found''${NC}"
              fi
              echo ""
            fi
          done
          
          # サマリー表示
          if [[ "$FORMAT" == "human" ]]; then
            echo -e "''${BOLD}Summary:''${NC}"
            echo -n "  Total: ''${#FILES[@]} file(s), "
            
            if [[ $TOTAL_ERRORS -eq 0 ]] && [[ $TOTAL_WARNINGS -eq 0 ]]; then
              echo -e "''${GREEN}all passed''${NC}"
              exit 0
            else
              echo -e "''${RED}$TOTAL_ERRORS error(s)''${NC}, ''${YELLOW}$TOTAL_WARNINGS warning(s)''${NC} in $FILES_WITH_ISSUES file(s)"
              exit 1
            fi
          elif [[ "$FORMAT" == "json" ]]; then
            echo '  ],'
            echo '  "summary": {'
            echo "    \"total_files\": ''${#FILES[@]},"
            echo "    \"files_with_issues\": $FILES_WITH_ISSUES,"
            echo "    \"total_errors\": $TOTAL_ERRORS,"
            echo "    \"total_warnings\": $TOTAL_WARNINGS"
            echo '  }'
            echo '}'
          fi
        '';

        # LSMCPラッパー（パターンマッチング対応）
        lsmcpCli = pkgs.writeShellScriptBin "lsmcp-cli" ''
          #!${pkgs.bash}/bin/bash
          set -euo pipefail
          
          # デフォルト値
          LANGUAGE=""
          PATTERN=""
          COMMAND="diagnostics"
          
          # 引数解析
          while [[ $# -gt 0 ]]; do
            case $1 in
              -l|--language)
                LANGUAGE="$2"
                shift 2
                ;;
              -p|--pattern)
                PATTERN="$2"
                shift 2
                ;;
              *)
                COMMAND="$1"
                shift
                ;;
            esac
          done
          
          # Python診断
          if [[ "$LANGUAGE" == "python" ]] && [[ "$COMMAND" == "diagnostics" ]]; then
            if [[ -z "$PATTERN" ]]; then
              echo "Error: Pattern required for Python diagnostics"
              echo "Usage: lsmcp-cli -l python -p '*.py' diagnostics"
              exit 1
            fi
            
            # パターンマッチング
            FILES=()
            while IFS= read -r -d "" file; do
              FILES+=("$file")
            done < <(find . -name "$PATTERN" -type f -print0)
            
            if [[ ''${#FILES[@]} -eq 0 ]]; then
              echo "No files found matching pattern: $PATTERN"
              exit 0
            fi
            
            # python-diagnosticsを実行
            exec ${pythonDiagnostics}/bin/python-diagnostics "''${FILES[@]}"
          else
            # その他の言語は通常のlsmcpを使用
            exec ${pkgs.nodejs}/bin/npx @mizchi/lsmcp "$@"
          fi
        '';

      in
      {
        packages = {
          default = lsmcpCli;
          python-diagnostics = pythonDiagnostics;
          lsmcp-cli = lsmcpCli;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs
            pythonEnv
            
            # Python開発ツール
            python3Packages.mypy
            python3Packages.black
            python3Packages.isort
            python3Packages.bandit
            ruff
            
            # TypeScript/JavaScript
            nodePackages.typescript
            nodePackages.typescript-language-server
            
            # その他のLSP
            rust-analyzer
            gopls
          ];
          
          shellHook = ''
            echo "LSMCP Development Environment"
            echo ""
            echo "Available commands:"
            echo "  lsmcp-cli        - Enhanced LSMCP CLI wrapper"
            echo "  python-diagnostics - Comprehensive Python file diagnostics"
            echo ""
            echo "Examples:"
            echo "  # Python diagnostics using wrapper"
            echo "  lsmcp-cli -l python -p '*.py' diagnostics"
            echo ""
            echo "  # Direct Python diagnostics"
            echo "  python-diagnostics main.py"
            echo "  python-diagnostics --check=type src/*.py"
            echo "  python-diagnostics --format=json main.py"
            echo ""
            echo "  # TypeScript diagnostics (original lsmcp)"
            echo "  npx @mizchi/lsmcp --include '**/*.ts' -l typescript"
          '';
        };
        
        # Nix app定義
        apps = {
          default = flake-utils.lib.mkApp {
            drv = lsmcpCli;
          };
          
          python-diagnostics = flake-utils.lib.mkApp {
            drv = pythonDiagnostics;
          };
        };
      }
    );
}