# 起動するアプリケーションとウィンドウ名の配列
aa_APPS=(
  "shell"
  "watch"
)

# ウィンドウを開く関数 (ウィンドウが存在しなければ作成し、アプリを起動)
aa_create_window() {
  local aa_window_id="$1"
  local app_name="${aa_APPS[$aa_window_id]}"
  local window_name="${app_name}"
  echo "ウィンドウ $aa_window_id ('$window_name') を作成します..."
  tmux new-window -t "$SESSION_NAME":"$aa_window_id" -n "$window_name"
}

aa_open_window() {
  local aa_window_id="$1"
  local app_name="${aa_APPS[$aa_window_id]}"
  local window_name="${app_name}"

  # ウィンドウでアプリが起動しているか確認 (プロセス名で判定)
  if ! tmux list-panes -t "$SESSION_NAME":"$aa_window_id" -F "#{pane_pid} #{pane_current_command}" | grep -q "$app_name"; then
    echo "ウィンドウ $aa_window_id ('$window_name') で '$app_name' が起動していません。ウィンドウを作成し、起動します..."
    aa_create_window "$aa_window_id"
    # aa_launch_app "$aa_window_id"
  else
    echo "ウィンドウ $aa_window_id ('$window_name') で '$app_name' は正常に起動しています。"
  fi
}

aa_launch_app() {
  local aa_window_id="$1"
  local app_name="${aa_APPS[$aa_window_id]}"
  echo "ウィンドウ $aa_window_id で '$app_name' を起動します..."
  tmux send-keys -t "$SESSION_NAME":"$aa_window_id" "$app_name ; tmux detach ; tmux kill-window" Enter
}

# セッション初期化関数 (新規セッション作成時にウィンドウを作成し、アプリを起動)
aa_session_init() {
  echo "tmux セッション '$SESSION_NAME' を新規作成します..."
  # tmux セッションを新規作成 (バックグラウンドで実行)
  tmux new-session -d -s "$SESSION_NAME"

  # アプリケーション配列に基づいてウィンドウを作成し、アプリを起動
  for aa_window_id in "${!aa_APPS[@]}"; do
    aa_open_window "$aa_window_id"
  done

  # 必要であれば、tmux 設定ファイルをリロード (タブ切り替え設定を反映)
  tmux source-file ~/.tmux.conf

  echo "tmux セッション '$SESSION_NAME' を作成し、アプリを起動しました。"
  echo "tmux にアタッチするには: tmux attach-session -t $SESSION_NAME"
  tmux attach-session -t $SESSION_NAME
}


# tmux セッションが存在するか確認
aa() {
  # tmux セッション名 (任意)
  SESSION_NAME=$(basename "$PWD")_aa
  echo SESSION_NAME $SESSION_NAME

  if tmux has-session -t "$SESSION_NAME" 2> /dev/null; then
    echo "tmux セッション '$SESSION_NAME' は既に存在します。"
    echo "既存のセッションにアタッチし、不足しているウィンドウを復元します..."

    # アプリケーション配列に基づいてウィンドウの存在を確認し、必要であれば作成
    for aa_window_id in "${!aa_APPS[@]}"; do
      aa_open_window "$aa_window_id"
    done

    tmux attach-session -t "$SESSION_NAME"

  else
    aa_session_init
  fi
}