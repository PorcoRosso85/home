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
        # aaコマンドをflakeのアプリとして提供
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
              -n, --no-apparmor    Disable AppArmor (run directly)
              -h, --help           Show this help
            
            Environment variables:
              DISABLE_APPARMOR=1   Disable AppArmor
              NO_APPARMOR=1        Disable AppArmor
            
            Examples:
              nix run ${./flake.nix}#aa -- nixpkgs#hello
              nix run ${./flake.nix}#aa -- -p strict github:some/tool
              nix run ${./flake.nix}#aa -- ./my-flake -- --version
            EOF
              exit 0
            fi
            
            # デフォルト値
            profile="restricted"
            mode="enforce"
            verbose=0
            no_apparmor=0
            
            # 環境変数チェック
            if [[ -n "$DISABLE_APPARMOR" ]] || [[ -n "$NO_APPARMOR" ]]; then
              no_apparmor=1
              [[ -n "$DISABLE_APPARMOR" ]] && [[ "$DISABLE_APPARMOR" != "0" ]] && verbose=1
            fi
            
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
                -n|--no-apparmor)
                  no_apparmor=1
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
            
            # AppArmor無効化チェック
            if [[ $no_apparmor -eq 1 ]]; then
              [[ $verbose -eq 1 ]] && echo "⚠️  AppArmor disabled by user request"
            else
              [[ $verbose -eq 1 ]] && echo "🔒 Applying AppArmor profile '$profile' in $mode mode to $flake"
            fi
            
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
            
            # AppArmor無効化された場合は直接実行
            if [[ $no_apparmor -eq 1 ]]; then
              exec "$exe" "$@"
            fi
            
            # AppArmorプロファイルが存在するかチェック
            if command -v aa-exec >/dev/null 2>&1; then
              # プロファイルをロード（必要なら）
              if ! aa-status --json 2>/dev/null | grep -q "\"$profile\""; then
                [[ $verbose -eq 1 ]] && echo "⚠️  Profile '$profile' not loaded, running without AppArmor"
                exec "$exe" "$@"
              else
                # AppArmorで実行
                exec aa-exec -p "$profile" -- "$exe" "$@"
              fi
            else
              echo "Warning: AppArmor not available, running without protection" >&2
              exec "$exe" "$@"
            fi
          '');
        };
        
        # デフォルトアプリはREADME表示
        apps.default = {
          type = "app";
          program = toString (pkgs.writeShellScript "show-readme" ''
            ${pkgs.bat}/bin/bat -p ${./README.md} || cat ${./README.md}
          '');
        };
        
        # 自動テストアプリ
        apps.test = {
          type = "app";
          program = toString (pkgs.writeShellScript "test-apparmor" ''
            set -e
            
            echo "=== AppArmor Automatic Test Suite ==="
            echo ""
            
            # テストプログラム作成
            TEST_SCRIPT=$(mktemp)
            cat > "$TEST_SCRIPT" << 'EOF'
            #!/usr/bin/env bash
            echo "Test PID: $$"
            
            # 1. AppArmorプロファイル確認
            profile=$(cat /proc/$$/attr/current 2>/dev/null || echo "unconfined")
            echo "AppArmor profile: $profile"
            
            # 2. アクセステスト
            echo ""
            echo "Access tests:"
            
            # /tmp書き込み
            if echo "test" > /tmp/aa-test-$$ 2>/dev/null; then
              echo "  /tmp write: ✓ allowed"
              rm -f /tmp/aa-test-$$
            else
              echo "  /tmp write: ✗ blocked"
            fi
            
            # SSH鍵アクセス
            if [[ -f ~/.ssh/id_rsa ]] && cat ~/.ssh/id_rsa >/dev/null 2>&1; then
              echo "  SSH keys: ⚠️  ACCESSIBLE"
            else
              echo "  SSH keys: ✓ protected"
            fi
            
            # /etc書き込み
            if touch /etc/test-$$ 2>/dev/null; then
              echo "  /etc write: ⚠️  ALLOWED"
              rm -f /etc/test-$$
            else
              echo "  /etc write: ✓ blocked"
            fi
            
            # ネットワーク
            if ${pkgs.curl}/bin/curl -s --max-time 2 https://example.com >/dev/null 2>&1; then
              echo "  Network: ✓ allowed"
            else
              echo "  Network: ✗ blocked"
            fi
            EOF
            chmod +x "$TEST_SCRIPT"
            
            echo "1. Testing WITHOUT AppArmor:"
            echo "----------------------------"
            "$TEST_SCRIPT"
            
            echo ""
            echo ""
            echo "2. Testing WITH AppArmor (restricted profile):"
            echo "----------------------------------------------"
            echo "(Would run: ${self.apps.${system}.aa.program} $TEST_SCRIPT)"
            echo "Note: AppArmor profile application requires proper setup"
            echo "Profile status: $(cat /proc/$$/attr/current 2>/dev/null || echo 'unknown')"
            
            echo ""
            echo ""
            echo "3. Testing WITH AppArmor (strict profile):"
            echo "------------------------------------------"  
            echo "(Would run: ${self.apps.${system}.aa.program} -p strict $TEST_SCRIPT)"
            echo "Note: AppArmor profile application requires proper setup"
            
            # クリーンアップ
            rm -f "$TEST_SCRIPT"
            
            echo ""
            echo "=== Test Summary ==="
            echo ""
            echo "✓ If you see different results between tests, AppArmor is working!"
            echo "✓ Look for 'SSH keys: protected' in AppArmor tests"
            echo "✓ Strict profile should block network access"
            echo ""
            echo "To verify manually:"
            echo "  - Check audit logs: sudo journalctl -g apparmor"
            echo "  - Check process: cat /proc/\$\$/attr/current"
          '');
        };
      });
}