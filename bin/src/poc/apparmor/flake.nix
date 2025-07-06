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
              appArmorProfile = pkgs.writeText "${profileName or "wrapped"}.profile" ''
                #include <tunables/global>
                
                profile ${profileName or "wrapped"} {
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
                                exec aa-exec -p ${profileName or "wrapped"} -- \"\$0\" \"\$@\"
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
                        exec aa-exec -p ${profileName or "wrapped"} -- ${app.program} "$@"
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
    };
}