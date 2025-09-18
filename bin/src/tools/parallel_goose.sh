#!/usr/bin/env bash
set -e

# @describe 複数のgooseジョブを並列に実行します
# @option --jobs! JSON形式のジョブリスト（例: '[{"jobId": 1, "text": "プロンプト1"}, {"jobId": 2, "text": "プロンプト2"}]'）
# @option --goose-args another_gooseに渡す共通引数
# @flag --dry-run 実行せずにコマンドを表示

# TODO:
# 1. MCPツール連携時の出力制御
#    - MCPツールとしての実行時、子プロセス（another_goose）の出力も標準出力に混在する問題を解決
#    - dry-runモードの出力がMCPツール経由では表示されない問題を解決
#
# 2. 子プロセスの出力制御
#    - バックグラウンド実行された子プロセスの出力を完全に制御する方法を実装
#    - MCPの仕組み上の標準出力/標準エラー出力の混在問題を解決
#
# 3. ジョブの進捗表示
#    - 各ジョブの進捗状況をリアルタイムで表示する機能の追加
#    - 長時間実行ジョブの状態確認方法の改善
#
# 4. MCPツール向けの特殊対応
#    - MCPツール特有の出力制御方法の調査と実装
#    - より深いMCP統合のための修正
#
# 5. 結果のフィルタリングオプション
#    - 出力サイズの制限オプションの追加
#    - 特定パターンによる結果のフィルタリング機能の実装
#
# 6. 進捗表示の改善
#    - ジョブの進捗状況を示すステータス更新機能の追加
#    - 長時間実行ジョブのタイムアウト設定の実装
#
# 7. ジョブリクエストのベストプラクティス
#    - goose_parallelを呼び出す際の動的なジョブ内容記載のベストプラクティスを提供
#    - descriptionの充実、フラグによるヘルプ表示の改善、実行時のアラート表示など
#    - 「各jobが完了時どの状態となっているべきか」を効果的にリクエストできる方法の提供

# argcの評価
eval "$(argc --argc-eval "$0" "$@")"

# スクリプトのディレクトリを取得
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 一時ディレクトリの設定
TMP_DIR=$(mktemp -d)
# 終了時に一時ディレクトリを削除
trap 'rm -rf "$TMP_DIR"' EXIT

# デバッグ情報をファイルに出力
{
  echo "argc_jobs = ${argc_jobs}"
  echo "argc_goose_args = ${argc_goose_args}"
  echo "argc_dry_run = ${argc_dry_run}"
} > "$TMP_DIR/debug.log"

# JSONパースのヘルパー関数
parse_json() {
  local json="$1"
  local field="$2"
  local jobId="$3"
  
  python3 -c "import json, sys; data = json.loads(sys.argv[1]); print([item['$field'] for item in data if item['jobId'] == $jobId][0])" "$json"
}

# ジョブIDのリストを取得
job_ids=$(python3 -c "import json, sys; print(' '.join(str(item['jobId']) for item in json.loads(sys.argv[1])))" "${argc_jobs}")

# ドライランモード時の結果を生成
if [ "${argc_dry_run}" = "1" ]; then
  commands=()
  for job_id in $job_ids; do
    job_text=$(parse_json "${argc_jobs}" "text" "$job_id")
    cmd="${SCRIPT_DIR}/another_goose.sh ${argc_goose_args} --text=\"$job_text\""
    commands+=("{\"jobId\": $job_id, \"dry_run\": true, \"command\": \"$cmd\"}")
  done
  
  # 結果をJSONとして出力
  echo "[$(IFS=,; echo "${commands[*]}")]"
  exit 0
fi

# 実行モードの処理
declare -A jobs_pids
declare -A jobs_status
declare -A jobs_output

# 各ジョブをバックグラウンドで実行
for job_id in $job_ids; do
  job_text=$(parse_json "${argc_jobs}" "text" "$job_id")
  output_file="$TMP_DIR/output_${job_id}.txt"
  
  # 実際のコマンドを構築
  cmd="${SCRIPT_DIR}/another_goose.sh ${argc_goose_args} --text=\"$job_text\""
  
  # コマンドを実行し、出力をファイルにリダイレクト
  eval "$cmd" > "$output_file" 2>&1 &
  
  # PIDを記録
  pid=$!
  jobs_pids["$job_id"]=$pid
  echo "Started job $job_id with PID $pid" >> "$TMP_DIR/debug.log"
done

# すべてのジョブが完了するのを待つ
for job_id in $job_ids; do
  pid=${jobs_pids["$job_id"]}
  wait $pid || true
  jobs_status["$job_id"]=$?
  echo "Job $job_id completed with status ${jobs_status["$job_id"]}" >> "$TMP_DIR/debug.log"
done

# 結果をJSON形式で構築
results=()
for job_id in $job_ids; do
  output_file="$TMP_DIR/output_${job_id}.txt"
  status=${jobs_status["$job_id"]}
  
  # 出力ファイルの内容を取得
  if [ -f "$output_file" ]; then
    # 内容を読み取り、JSONでエスケープ
    output=$(cat "$output_file" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
  else
    output="Error: No output file found"
  fi
  
  # JSONオブジェクトを作成
  results+=("{\"jobId\": $job_id, \"status\": $status, \"output\": \"$output\"}")
done

# 最終的なJSONを出力
echo "[$(IFS=,; echo "${results[*]}")]"

exit 0
