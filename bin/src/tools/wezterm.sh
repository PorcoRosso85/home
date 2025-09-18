 # 定数定義
 WEZTERM_PATH="/mnt/c/Program Files/WezTerm/wezterm.exe"
 WSL_DISTRO="nix"

 # 親ターミナルを分割する関数
 split_parent_terminal() {
     local dir="$1"
     "$WEZTERM_PATH" cli split-pane --right --percent 10 -- wsl -d "$WSL_DISTRO" --cd "$dir" -- /usr/bin/env bash -c "$2"
 }

 # 子ウィンドウ内で分割を実行するコマンドを生成する関数
 generate_child_command() {
     local dir="$1"
    
     # エスケープを適切に処理
     echo "cd \"$dir\" && \"$WEZTERM_PATH\" cli split-pane --horizontal --percent 60 -- wsl -d $WSL_DISTRO --cd \"$dir\" -- /usr/bin/env bash && exec bash"
 }

 # 各ディレクトリに対する処理を行う関数
 process_directory() {
     local dir="$1"
    
     # ディレクトリが存在するか確認
     if [ ! -d "$dir" ]; then
         echo "エラー: ディレクトリ '$dir' は存在しません。"
         return 1
     fi
    
     # 絶対パスに変換
     dir=$(realpath "$dir")
    
     # 親2のターミナルで実行するコマンド
     local parent2_command="\"$WEZTERM_PATH\" start -- wsl -d $WSL_DISTRO --cd \"$dir\" -- /usr/bin/env bash -c '$(generate_child_command "$dir")'; exec bash"
    
     # 親ターミナルの分割と子ウィンドウの起動を実行
     split_parent_terminal "$dir" "$parent2_command"
 }

 # メイン処理
 main() {
     # 引数がなければ現在のディレクトリを使用
     if [ $# -eq 0 ]; then
         process_directory "$(pwd)"
     else
         # 各ディレクトリに対して処理を実行
         for dir in "$@"; do
             process_directory "$dir"
         done
     fi
 }

 # スクリプトの実行
 main "$@"
