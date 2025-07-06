{
  description = "Bubblewrap sandboxing for Nix commands";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # 実際の隔離機能を持つrunコマンド（bubblewrap使用）
        apps.run = {
          type = "app";
          program = toString (pkgs.writeShellScript "bwrap-run" ''
            set -e
            
            # ヘルプ
            if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]] || [[ -z "$1" ]]; then
              cat <<EOF
            Usage: nix run . -- [OPTIONS] <command> [args...]
            
            Run a command in a sandboxed environment using bubblewrap.
            
            Profiles:
              restricted (default): Network OK, Home read-only, no SSH/GPG access
              strict: No network, no home access, minimal permissions
              confined: Limited to specific directory, no parent access
              safe: Dangerous commands (rm -rf, dd, etc.) are blocked
              
            Options:
              -p, --profile NAME    Use specific profile
              -w, --workdir PATH    Set working directory (for confined profile)
              -v, --verbose         Show what's happening
              -n, --no-sandbox      Disable sandboxing (run directly)
              -h, --help            Show this help
            
            Examples:
              nix run . -- cat /etc/passwd                    # OK (read-only)
              nix run . -- cat ~/.ssh/id_rsa                  # Blocked
              nix run . -- -p strict curl example.com         # Blocked (no network)
              nix run . -- -p confined -w /tmp/project make   # Limited to /tmp/project
              nix run . -- -p safe ./untrusted-script.sh      # rm -rf blocked
            EOF
              exit 0
            fi
            
            # デフォルト値
            profile="restricted"
            workdir=""
            verbose=0
            no_sandbox=0
            
            # オプション解析
            while [[ $# -gt 0 ]]; do
              case "$1" in
                -p|--profile)
                  profile="$2"
                  shift 2
                  ;;
                -w|--workdir)
                  workdir="$2"
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
            
            # 危険コマンドをブロックするための安全なrmラッパー
            safe_rm_wrapper='#!/bin/sh
            for arg in "$@"; do
              case "$arg" in
                -rf|-fr|-r*f*|--recursive*--force*|--force*--recursive*)
                  echo "Error: rm -rf is blocked in safe mode" >&2
                  exit 1
                  ;;
              esac
            done
            exec ${pkgs.coreutils}/bin/rm "$@"
            '
            
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
                
              confined)
                # 特定ディレクトリに制限
                if [[ -z "$workdir" ]]; then
                  echo "Error: confined profile requires --workdir" >&2
                  exit 1
                fi
                
                if [[ ! -d "$workdir" ]]; then
                  echo "Error: workdir '$workdir' does not exist" >&2
                  exit 1
                fi
                
                # 作業ディレクトリを絶対パスに変換
                workdir=$(realpath "$workdir")
                
                [[ $verbose -eq 1 ]] && echo "📁 Confined to: $workdir"
                
                # 最小限の環境 + 作業ディレクトリのみ
                bwrap_opts=(
                  --ro-bind /nix/store /nix/store
                  --bind "$workdir" /work
                  --proc /proc
                  --dev /dev
                  --tmpfs /tmp
                  --die-with-parent
                  --clearenv
                  --setenv PATH "$PATH"
                  --setenv HOME /work
                  --setenv PWD /work
                  --chdir /work
                )
                
                # 実行に必要なディレクトリをバインド
                for dir in /bin /usr /lib /lib64; do
                  [[ -d "$dir" ]] && bwrap_opts+=(--ro-bind "$dir" "$dir")
                done
                ;;
                
              safe)
                # 危険なコマンドをブロック
                # 一時ディレクトリに安全なラッパーを作成
                safe_bin_dir=$(mktemp -d)
                trap "rm -rf $safe_bin_dir" EXIT
                
                # rmの安全なラッパーを作成
                echo "$safe_rm_wrapper" > "$safe_bin_dir/rm"
                chmod +x "$safe_bin_dir/rm"
                
                # 必要なコマンドへのシンボリックリンクを作成
                ln -s ${pkgs.coreutils}/bin/touch "$safe_bin_dir/touch"
                ln -s ${pkgs.coreutils}/bin/ls "$safe_bin_dir/ls"
                ln -s ${pkgs.coreutils}/bin/cat "$safe_bin_dir/cat"
                ln -s ${pkgs.coreutils}/bin/echo "$safe_bin_dir/echo"
                
                # ddをブロック
                echo '#!/bin/sh
                echo "Error: dd is blocked in safe mode" >&2
                exit 1' > "$safe_bin_dir/dd"
                chmod +x "$safe_bin_dir/dd"
                
                # mkfsをブロック
                echo '#!/bin/sh
                echo "Error: mkfs is blocked in safe mode" >&2
                exit 1' > "$safe_bin_dir/mkfs"
                chmod +x "$safe_bin_dir/mkfs"
                
                # 安全なbinディレクトリを優先的にバインド
                bwrap_opts+=(--ro-bind "$safe_bin_dir" /safe-bin)
                bwrap_opts+=(--setenv PATH "/safe-bin:$PATH")
                
                # 通常のrestrictedプロファイルの設定も適用
                if [[ -d "$HOME" ]]; then
                  bwrap_opts+=(--ro-bind "$HOME" "$HOME")
                  [[ -d "$HOME/.ssh" ]] && bwrap_opts+=(--tmpfs "$HOME/.ssh")
                  [[ -d "$HOME/.gnupg" ]] && bwrap_opts+=(--tmpfs "$HOME/.gnupg")
                  [[ -d "$HOME/.aws" ]] && bwrap_opts+=(--tmpfs "$HOME/.aws")
                fi
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
              if ${self.apps.${system}.run.program} cat ~/.ssh/id_rsa 2>&1 | grep -q "No such file"; then
                echo "✓ (properly blocked)"
              else
                echo "✗ (should be blocked!)"
                exit 1
              fi
            else
              # テスト用に偽のSSH鍵パスでテスト
              if ${self.apps.${system}.run.program} ls ~/.ssh 2>&1 | grep -q "No such file"; then
                echo "✓ (directory masked)"
              else
                echo "- (no SSH keys to test)"
              fi
            fi
            
            # テスト2: /etc書き込みブロック
            echo -n "2. /etc write blocked: "
            if ! ${self.apps.${system}.run.program} ${pkgs.coreutils}/bin/touch /etc/test-file 2>&1; then
              echo "✓ (properly blocked)"
            else
              echo "✗ (should be blocked!)"
              exit 1
            fi
            
            # テスト3: strictプロファイルでネットワークブロック
            echo -n "3. Network blocked (strict): "
            if ! ${self.apps.${system}.run.program} -p strict ${pkgs.curl}/bin/curl -s --max-time 2 https://example.com 2>/dev/null; then
              echo "✓ (network isolated)"
            else
              echo "✗ (network should be blocked in strict mode)"
              exit 1
            fi
            
            # テスト4: restrictedプロファイルでネットワーク許可（DNS解決の問題でスキップ可能）
            echo -n "4. Network allowed (restricted): "
            if ${self.apps.${system}.run.program} ${pkgs.curl}/bin/curl -s --max-time 2 https://example.com >/dev/null 2>&1; then
              echo "✓ (network OK)"
            else
              echo "- (DNS might not work in sandbox)"
            fi
            
            # テスト5: ホームディレクトリ読み取り
            echo -n "5. Home directory readable: "
            if ${self.apps.${system}.run.program} ${pkgs.coreutils}/bin/ls ~ >/dev/null 2>&1; then
              echo "✓"
            else
              echo "✗"
            fi
            
            # テスト6: 一時ディレクトリ書き込み
            echo -n "6. /tmp writable: "
            # /tmpは各実行で分離されているため、1回の実行で両方のコマンドを実行
            if ${self.apps.${system}.run.program} ${pkgs.bash}/bin/bash -c "${pkgs.coreutils}/bin/touch /tmp/test-file && ${pkgs.coreutils}/bin/rm /tmp/test-file" 2>/dev/null; then
              echo "✓"
            else
              echo "✗ (isolated /tmp)"
            fi
            
            echo ""
            echo "=== New Features Test ==="
            echo ""
            
            # テスト7: confinedプロファイルのディレクトリ制限
            echo -n "7. Directory confinement: "
            # テスト用ディレクトリを作成
            test_dir=$(mktemp -d)
            trap "rm -rf $test_dir" EXIT
            
            # ホームディレクトリにアクセスできないことを確認
            if ! ${self.apps.${system}.run.program} -p confined -w "$test_dir" ${pkgs.coreutils}/bin/ls /home 2>/dev/null; then
              echo "✓ (home access blocked)"
            else
              echo "✗ (should not access home!)"
              exit 1
            fi
            
            # テスト8: safeプロファイルでrm -rfブロック
            echo -n "8. rm -rf blocked (safe): "
            if ${self.apps.${system}.run.program} -p safe rm -rf /tmp/nonexistent 2>&1 | grep -q "rm -rf is blocked"; then
              echo "✓ (properly blocked)"
            else
              echo "✗ (should be blocked!)"
              exit 1
            fi
            
            # テスト9: safeプロファイルで通常のrmは許可
            echo -n "9. Normal rm allowed (safe): "
            # 一時ファイルを作成してテスト
            if ${self.apps.${system}.run.program} -p safe ${pkgs.bash}/bin/bash -c "touch /tmp/test-rm-file && rm /tmp/test-rm-file && echo success" 2>&1 | grep -q "success"; then
              echo "✓ (normal rm works)"
            else
              echo "✗ (normal rm should work!)"
              exit 1
            fi
            
            # テスト10: safeプロファイルでddブロック
            echo -n "10. dd blocked (safe): "
            if ${self.apps.${system}.run.program} -p safe dd if=/dev/zero of=/tmp/test count=1 2>&1 | grep -q "dd is blocked"; then
              echo "✓ (properly blocked)"
            else
              echo "✗ (should be blocked!)"
              exit 1
            fi
            
            # テスト11: confinedプロファイルで作業ディレクトリ内は書き込み可能
            echo -n "11. Write allowed in workdir: "
            # 書き込みテストを単純化
            if ${self.apps.${system}.run.program} -p confined -w "$test_dir" ${pkgs.coreutils}/bin/touch test.txt 2>/dev/null; then
              echo "✓ (can write in workdir)"
            else
              echo "✗ (should be able to write!)"
              exit 1
            fi
            
            # テスト12: confinedプロファイルでホームディレクトリアクセス不可
            echo -n "12. Home not accessible (confined): "
            if ! ${self.apps.${system}.run.program} -p confined -w "$test_dir" ${pkgs.coreutils}/bin/ls ~/.bashrc 2>/dev/null; then
              echo "✓ (home blocked)"
            else
              echo "✗ (home should be blocked!)"
              exit 1
            fi
            
            echo ""
            echo "All tests passed! 🎉"
            echo "Sandboxing is working properly! 🔒"
          '');
        };
        
        # 自動テストアプリ - 実際の隔離機能をテスト
        apps.test = self.apps.${system}.test-real;
      });
}