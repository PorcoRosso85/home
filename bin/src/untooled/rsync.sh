#!/usr/bin/env rsync

# 引数チェック
if [ $# -ne 2 ]; then
    echo "Usage: $0 <source_path> <target_path>"
    exit 1
fi

# 引数から同期元と同期先のパスを取得
LOCAL_PATH="$1"
REMOTE_PATH="$2"

# ログファイルの設定
LOG_DIR="/var/log/rsync"
LOG_FILE="${LOG_DIR}/rsync_$(date +%Y%m%d_%H%M%S).log"

# ログディレクトリが存在しない場合は作成
mkdir -p "${LOG_DIR}"

# Tailscale接続先を使用
REMOTE_HOST="${SSH_WIN_USER}@${SSH_IP}"

# rsyncオプション
# -a: アーカイブモード（再帰的にコピー、パーミッション、タイムスタンプ等を保持）
# -v: 詳細出力
# -z: 圧縮を有効化
# --delete: 送信先に存在しないファイルを削除
# --exclude: 同期から除外するファイルやディレクトリ

rsync -avz \
    -e "ssh -p ${SSH_PORT}" \
    --delete \
    --exclude '.git' \
    --exclude '.DS_Store' \
    --log-file="${LOG_FILE}" \
    "${LOCAL_PATH}/" \
    "${REMOTE_HOST}:${REMOTE_PATH}"

# 終了ステータスの確認
if [ $# -eq 2 ] && [ $? -eq 0 ]; then
    echo "Rsync completed successfully"
else
    echo "Rsync encountered an error"
    exit 1
fi