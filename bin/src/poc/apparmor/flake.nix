{
  description = "AppArmor wrapper for Nix flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    {
      # AppArmorでflakeをラップする関数
      lib.wrapFlakeWithAppArmor = { 
        flake,              # ラップ対象のflake
        profilePath ? null, # カスタムプロファイルのパス
        profileName ? null, # プロファイル名
        enforceMode ? false # true: enforce, false: complain
      }: 
        let
          # 元のflakeのoutputsを取得
          originalOutputs = flake.outputs;
          
          # システムごとの処理
          wrapSystem = system: 
            let
              pkgs = nixpkgs.legacyPackages.${system};
              
              # AppArmorプロファイルの生成
              appArmorProfile = pkgs.writeText "${if profileName != null then profileName else "wrapped"}.profile" ''
                #include <tunables/global>
                
                profile ${if profileName != null then profileName else "wrapped"} {
                  #include <abstractions/base>
                  
                  # 基本的な権限
                  /nix/store/** r,
                  /proc/sys/kernel/random/uuid r,
                  /dev/urandom r,
                  
                  # カスタムプロファイルがある場合は読み込む
                  ${if profilePath != null then "#include \"${profilePath}\"" else ""}
                  
                  # デフォルトの制限
                  deny network,
                  deny /home/** rw,
                  deny /etc/** w,
                }
              '';
              
              # パッケージをAppArmorでラップする関数
              wrapPackage = pkg: 
                if pkg ? type && pkg.type == "derivation" then
                  pkgs.symlinkJoin {
                    name = "${pkg.name}-apparmor-wrapped";
                    paths = [ pkg ];
                    buildInputs = [ pkgs.makeWrapper ];
                    postBuild = ''
                      # 実行ファイルをラップ
                      for exe in $out/bin/*; do
                        if [ -f "$exe" ] && [ -x "$exe" ]; then
                          wrapProgram "$exe" \
                            --run "
                              # AppArmorプロファイルをロード（権限が必要）
                              if command -v aa-exec >/dev/null 2>&1; then
                                exec aa-exec -p ${if profileName != null then profileName else "wrapped"} -- \"\$0\" \"\$@\"
                              else
                                echo 'Warning: aa-exec not found, running without AppArmor' >&2
                                exec \"\$0\" \"\$@\"
                              fi
                            "
                        fi
                      done
                    '';
                  }
                else
                  pkg;
              
              # アプリをAppArmorでラップする関数  
              wrapApp = app:
                if app ? program then
                  app // {
                    program = toString (pkgs.writeShellScript "${app.type or "app"}-wrapped" ''
                      if command -v aa-exec >/dev/null 2>&1; then
                        exec aa-exec -p ${if profileName != null then profileName else "wrapped"} -- ${app.program} "$@"
                      else
                        echo 'Warning: aa-exec not found, running without AppArmor' >&2
                        exec ${app.program} "$@"
                      fi
                    '');
                  }
                else
                  app;
                  
            in {
              # packagesをラップ
              packages = 
                if originalOutputs ? ${system} && originalOutputs.${system} ? packages then
                  builtins.mapAttrs (name: pkg: wrapPackage pkg) originalOutputs.${system}.packages
                else
                  {};
                  
              # appsをラップ
              apps = 
                if originalOutputs ? ${system} && originalOutputs.${system} ? apps then
                  builtins.mapAttrs (name: app: wrapApp app) originalOutputs.${system}.apps
                else
                  {};
                  
              # devShellsはそのまま（開発環境では通常AppArmorは不要）
              devShells = 
                if originalOutputs ? ${system} && originalOutputs.${system} ? devShells then
                  originalOutputs.${system}.devShells
                else
                  {};
            };
            
        in
          # flake-utilsのeachDefaultSystemを使う場合
          if originalOutputs ? packages || originalOutputs ? apps || originalOutputs ? devShells then
            flake-utils.lib.eachDefaultSystem wrapSystem
          # 直接システムごとに定義されている場合
          else
            builtins.mapAttrs (system: outputs: 
              if builtins.match ".*-linux" system != null then
                wrapSystem system
              else
                outputs
            ) originalOutputs;
            
      # 使用例を示すサンプルアプリ
      examples = {
        # readabilityをAppArmorでラップする例
        readabilityWrapped = self.lib.wrapFlakeWithAppArmor {
          flake = builtins.getFlake "/home/nixos/bin/src/poc/readability";
          profileName = "readability-restricted";
          enforceMode = false;
        };
        
        # similarityをAppArmorでラップする例
        similarityWrapped = self.lib.wrapFlakeWithAppArmor {
          flake = builtins.getFlake "/home/nixos/bin/src/poc/similarity";
          profileName = "similarity-restricted";
          profilePath = ./profiles/similarity.profile;
          enforceMode = false;
        };
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # aaコマンドをflakeのアプリとして提供（概念実証）
        apps.aa = {
          type = "app";
          program = toString (pkgs.writeShellScript "aa" ''
            set -e
            
            # ヘルプ
            if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]] || [[ -z "$1" ]]; then
              cat <<EOF
            Usage: nix run ${./flake.nix}#aa -- [OPTIONS] <flake-ref> [-- <args>...]
            
            Run a flake with AppArmor profile applied.
            
            Options:
              -p, --profile NAME    Use specific AppArmor profile (default: restricted)
              -c, --complain       Use complain mode instead of enforce
              -v, --verbose        Show what's happening
              -h, --help           Show this help
            
            Examples:
              nix run ${./flake.nix}#aa -- nixpkgs#hello
              nix run ${./flake.nix}#aa -- -p strict github:some/tool
              nix run ${./flake.nix}#aa -- ./my-flake -- --version
            
            Note: This is a proof of concept. AppArmor requires OS-level setup to function.
            EOF
              exit 0
            fi
            
            # デフォルト値
            profile="restricted"
            mode="enforce"
            verbose=0
            
            # オプション解析
            while [[ $# -gt 0 ]]; do
              case "$1" in
                -p|--profile)
                  profile="$2"
                  shift 2
                  ;;
                -c|--complain)
                  mode="complain"
                  shift
                  ;;
                -v|--verbose)
                  verbose=1
                  shift
                  ;;
                --)
                  shift
                  break
                  ;;
                -*)
                  echo "Unknown option: $1" >&2
                  exit 1
                  ;;
                *)
                  flake="$1"
                  shift
                  break
                  ;;
              esac
            done
            
            [[ $verbose -eq 1 ]] && echo "🔒 AppArmor POC: Would apply profile '$profile' in $mode mode"
            
            # flakeをビルド
            if [[ "$flake" == /* ]] || [[ "$flake" == ./* ]]; then
              store_path=$(nix build --no-link --print-out-paths "$flake")
            else
              store_path=$(nix build --no-link --print-out-paths "$flake" 2>/dev/null || \
                           nix build --no-link --print-out-paths "$flake#defaultPackage.${system}")
            fi
            
            # 実行ファイルを探す
            if [[ -d "$store_path/bin" ]]; then
              exe=$(find "$store_path/bin" -type f -executable | head -1)
            else
              echo "Error: No executable found in $store_path" >&2
              exit 1
            fi
            
            [[ $verbose -eq 1 ]] && echo "📦 Built: $store_path"
            [[ $verbose -eq 1 ]] && echo "🚀 Executing: $exe"
            
            # AppArmorプロファイルが存在するかチェック（POCなので実際には適用しない）
            if command -v aa-exec >/dev/null 2>&1; then
              [[ $verbose -eq 1 ]] && echo "ℹ️  aa-exec is available (but POC won't use it)"
            else
              [[ $verbose -eq 1 ]] && echo "ℹ️  aa-exec not available"
            fi
            
            # 実際には通常実行（POCのため）
            [[ $verbose -eq 1 ]] && echo "⚠️  Note: Running without actual AppArmor (POC)"
            exec "$exe" "$@"
          '');
        };
        
        # デフォルトアプリはREADME表示
        apps.default = {
          type = "app";
          program = toString (pkgs.writeShellScript "show-readme" ''
            ${pkgs.bat}/bin/bat -p ${./README.md} || cat ${./README.md}
          '');
        };
        
        # テストアプリ（POCの動作確認）
        apps.test = {
          type = "app";
          program = toString (pkgs.writeShellScript "test-apparmor-poc" ''
            echo "=== AppArmor POC Test ==="
            echo ""
            echo "This is a proof of concept for AppArmor integration with Nix."
            echo "Actual AppArmor functionality requires OS-level configuration."
            echo ""
            
            # 基本的な動作確認
            echo -n "1. aa command exists: "
            if ${self.apps.${system}.aa.program} ${pkgs.hello}/bin/hello >/dev/null 2>&1; then
              echo "✓"
            else
              echo "✗"
              exit 1
            fi
            
            echo -n "2. Verbose mode works: "
            if ${self.apps.${system}.aa.program} -v ${pkgs.coreutils}/bin/true 2>&1 | grep -q "AppArmor POC"; then
              echo "✓"
            else
              echo "✗"
              exit 1
            fi
            
            echo -n "3. Profile option works: "
            if ${self.apps.${system}.aa.program} -p custom -v ${pkgs.coreutils}/bin/true 2>&1 | grep -q "profile 'custom'"; then
              echo "✓"
            else
              echo "✗"
              exit 1
            fi
            
            echo ""
            echo "POC tests passed! ✅"
            echo ""
            echo "Note: This POC demonstrates the API design."
            echo "For actual sandboxing, see poc/bubblewrap."
          '');
        };
      });
}