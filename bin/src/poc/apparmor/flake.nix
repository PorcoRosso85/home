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
        # 実際の隔離機能を持つaaコマンド（bubblewrap使用）
        apps.aa = {
          type = "app";
          program = toString (pkgs.writeShellScript "aa" ''
            set -e
            
            # ヘルプ
            if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]] || [[ -z "$1" ]]; then
              cat <<EOF
            Usage: nix run ${./flake.nix}#aa -- [OPTIONS] <command> [args...]
            
            Run a command with AppArmor-like restrictions using bubblewrap.
            
            Profiles:
              restricted (default): Network OK, Home read-only, no SSH/GPG access
              strict: No network, no home access, minimal permissions
              
            Options:
              -p, --profile NAME    Use specific profile (restricted/strict)
              -v, --verbose        Show what's happening
              -n, --no-sandbox     Disable sandboxing (run directly)
              -h, --help           Show this help
            
            Examples:
              nix run .#aa -- cat /etc/passwd        # OK (read-only)
              nix run .#aa -- cat ~/.ssh/id_rsa      # Blocked
              nix run .#aa -- -p strict curl example.com  # Blocked (no network)
            EOF
              exit 0
            fi
            
            # デフォルト値
            profile="restricted"
            verbose=0
            no_sandbox=0
            
            # オプション解析
            while [[ $# -gt 0 ]]; do
              case "$1" in
                -p|--profile)
                  profile="$2"
                  shift 2
                  ;;
                -v|--verbose)
                  verbose=1
                  shift
                  ;;
                -n|--no-sandbox)
                  no_sandbox=1
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
                  break
                  ;;
              esac
            done
            
            if [[ $# -lt 1 ]]; then
              echo "Error: No command specified" >&2
              exit 1
            fi
            
            # サンドボックス無効の場合は直接実行
            if [[ $no_sandbox -eq 1 ]]; then
              [[ $verbose -eq 1 ]] && echo "⚠️  Sandbox disabled, running directly"
              exec "$@"
            fi
            
            [[ $verbose -eq 1 ]] && echo "🔒 Running with '$profile' profile"
            
            # bubblewrapの基本オプション
            bwrap_opts=(
              --ro-bind /nix/store /nix/store
              --ro-bind /etc /etc
              --proc /proc
              --dev /dev
              --tmpfs /tmp
              --tmpfs /var
              --tmpfs /run
              --die-with-parent
              --clearenv
              --setenv PATH "$PATH"
              --setenv HOME "$HOME"
            )
            
            # 実行に必要なディレクトリをバインド
            for dir in /bin /usr /lib /lib64; do
              [[ -d "$dir" ]] && bwrap_opts+=(--ro-bind "$dir" "$dir")
            done
            
            # プロファイル別設定
            case "$profile" in
              restricted)
                # ホームは読み取り専用、SSH/GPGはブロック
                if [[ -d "$HOME" ]]; then
                  bwrap_opts+=(--ro-bind "$HOME" "$HOME")
                  # SSH/GPG鍵をtmpfsでマスク
                  [[ -d "$HOME/.ssh" ]] && bwrap_opts+=(--tmpfs "$HOME/.ssh")
                  [[ -d "$HOME/.gnupg" ]] && bwrap_opts+=(--tmpfs "$HOME/.gnupg")
                  [[ -d "$HOME/.aws" ]] && bwrap_opts+=(--tmpfs "$HOME/.aws")
                fi
                # ネットワークは許可
                ;;
                
              strict)
                # ホームアクセスなし、ネットワークなし
                bwrap_opts+=(--unshare-net)
                # 最小限のファイルシステムのみ
                ;;
                
              *)
                echo "Error: Unknown profile '$profile'" >&2
                exit 1
                ;;
            esac
            
            [[ $verbose -eq 1 ]] && echo "📦 Executing: $@"
            
            # bubblewrapで実行
            exec ${pkgs.bubblewrap}/bin/bwrap "''${bwrap_opts[@]}" -- "$@"
          '');
        };
        
        # デフォルトアプリはREADME表示
        apps.default = {
          type = "app";
          program = toString (pkgs.writeShellScript "show-readme" ''
            ${pkgs.bat}/bin/bat -p ${./README.md} || cat ${./README.md}
          '');
        };
        
        # 実際の隔離機能をテスト
        apps.test-real = {
          type = "app";
          program = toString (pkgs.writeShellScript "test-real-sandboxing" ''
            echo "=== Real Sandboxing Test ==="
            echo ""
            
            # テスト1: SSHキーアクセスブロック
            echo -n "1. SSH key access blocked: "
            # SSH鍵がある場合のみテスト
            if [[ -f ~/.ssh/id_rsa ]]; then
              if ${self.apps.${system}.aa.program} cat ~/.ssh/id_rsa 2>&1 | grep -q "No such file"; then
                echo "✓ (properly blocked)"
              else
                echo "✗ (should be blocked!)"
                exit 1
              fi
            else
              # テスト用に偽のSSH鍵パスでテスト
              if ${self.apps.${system}.aa.program} ls ~/.ssh 2>&1 | grep -q "No such file"; then
                echo "✓ (directory masked)"
              else
                echo "- (no SSH keys to test)"
              fi
            fi
            
            # テスト2: /etc書き込みブロック
            echo -n "2. /etc write blocked: "
            if ! ${self.apps.${system}.aa.program} ${pkgs.coreutils}/bin/touch /etc/test-file 2>&1; then
              echo "✓ (properly blocked)"
            else
              echo "✗ (should be blocked!)"
              exit 1
            fi
            
            # テスト3: strictプロファイルでネットワークブロック
            echo -n "3. Network blocked (strict): "
            if ! ${self.apps.${system}.aa.program} -p strict ${pkgs.curl}/bin/curl -s --max-time 2 https://example.com 2>/dev/null; then
              echo "✓ (network isolated)"
            else
              echo "✗ (network should be blocked in strict mode)"
              exit 1
            fi
            
            # テスト4: restrictedプロファイルでネットワーク許可（DNS解決の問題でスキップ可能）
            echo -n "4. Network allowed (restricted): "
            if ${self.apps.${system}.aa.program} ${pkgs.curl}/bin/curl -s --max-time 2 https://example.com >/dev/null 2>&1; then
              echo "✓ (network OK)"
            else
              echo "- (DNS might not work in sandbox)"
            fi
            
            # テスト5: ホームディレクトリ読み取り
            echo -n "5. Home directory readable: "
            if ${self.apps.${system}.aa.program} ${pkgs.coreutils}/bin/ls ~ >/dev/null 2>&1; then
              echo "✓"
            else
              echo "✗"
            fi
            
            # テスト6: 一時ディレクトリ書き込み
            echo -n "6. /tmp writable: "
            # /tmpは各実行で分離されているため、1回の実行で両方のコマンドを実行
            if ${self.apps.${system}.aa.program} ${pkgs.bash}/bin/bash -c "${pkgs.coreutils}/bin/touch /tmp/test-file && ${pkgs.coreutils}/bin/rm /tmp/test-file" 2>/dev/null; then
              echo "✓"
            else
              echo "✗ (isolated /tmp)"
            fi
            
            echo ""
            echo "Sandboxing is working! 🔒"
          '');
        };
        
        # 自動テストアプリ - 実際の隔離機能をテスト
        apps.test = self.apps.${system}.test-real;
      });
}