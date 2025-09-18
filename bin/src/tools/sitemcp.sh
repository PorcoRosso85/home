#!/usr/bin/env -S nix shell nixpkgs#nodejs nixpkgs#argc --command bash

# @describe ウェブサイト全体を取得してMCPサーバー用のキャッシュを作成するツールです。キャッシュ結果は `~/.cache/sitemcp` に保存されます。もしキャッシュ先が出力されなかったらこちらを探索してください。
# @option --url! 取得するウェブサイトのURL
# @option --concurrency <INT> 同時リクエスト数（デフォルト: 5）
# @option --tool-name-strategy[domain|subdomain|pathname] ツール名生成戦略（デフォルト: domain）
# @option --match* 特定のページに一致するパターン
# @option --content-selector コンテンツ抽出用のCSSセレクタ
# @flag --no-cache キャッシングを無効にする
# @flag --show-config MCPサーバー設定情報を表示する

eval "$(argc --argc-eval "$0" "$@")"

echo "サイト $argc_url からデータを取得しています..."

# マッチパターンをコマンドライン引数として構築
match_args=""
if [[ ${#argc_match[@]} -gt 0 ]]; then
  for pattern in "${argc_match[@]}"; do
    match_args="$match_args -m \"$pattern\""
  done
fi

# コンテンツセレクタ引数の構築
content_selector_arg=""
if [[ -n "$argc_content_selector" ]]; then
  content_selector_arg="--content-selector \"$argc_content_selector\""
fi

# no-cacheフラグの処理
no_cache_arg=""
if [[ "$argc_no_cache" == "true" ]]; then
  no_cache_arg="--no-cache"
fi

# コマンドの構築と実行
cmd="pnpm dlx sitemcp \"$argc_url\" --concurrency ${argc_concurrency:-5} --tool-name-strategy ${argc_tool_name_strategy:-domain} $match_args $content_selector_arg $no_cache_arg"

echo "実行コマンド: $cmd"
eval "$cmd"

# 実行後の情報表示
if [[ $? -eq 0 ]]; then
  # ドメイン名からファイル名を推測
  site_domain=$(echo "$argc_url" | sed -E 's/https?:\/\///' | sed -E 's/\/.*//')
  cache_file_name=$(echo "$site_domain" | tr '.' '-')"-github-io.json"
  cache_full_path="$HOME/.cache/sitemcp/$cache_file_name"
  
  # キャッシュファイルの存在確認
  if [[ -f "$cache_full_path" ]]; then
    echo "キャッシュファイル: $cache_full_path"
    echo "サイズ: $(du -h "$cache_full_path" | cut -f1)"
    echo "作成日時: $(stat -c %y "$cache_full_path")"
  else
    # ディレクトリ内の最新ファイルを探す
    latest_file=$(find "$HOME/.cache/sitemcp" -type f -name "*.json" -printf "%T@ %p\n" | sort -n | tail -1 | cut -d' ' -f2-)
    if [[ -n "$latest_file" ]]; then
      echo "キャッシュファイル: $latest_file"
      echo "サイズ: $(du -h "$latest_file" | cut -f1)"
      echo "作成日時: $(stat -c %y "$latest_file")"
    else
      echo "キャッシュディレクトリ: $HOME/.cache/sitemcp/"
    fi
  fi
  
  # ツール名の取得（シンプルな推測）
  if [ -n "$argc_show_config" ]; then
    # NOTE: この部分は--show-configフラグが指定された場合のみ表示
    site_domain=$(echo "$argc_url" | sed -E 's/https?:\/\///' | sed -E 's/\/.*//')
    
    case "${argc_tool_name_strategy:-domain}" in
      domain)
        tool_name=$(echo "$site_domain" | cut -d. -f1 | sed 's/^./\U&\E/')
        ;;
      subdomain)
        tool_name=$(echo "$site_domain" | cut -d. -f1 | sed 's/^./\U&\E/')
        if [[ "$site_domain" == *"."*"."* ]]; then
          tool_name=$(echo "$site_domain" | sed -E 's/^([^.]+)\.([^.]+)\..+$/\1\2/' | sed 's/^./\U&\E/' | sed 's/\.//')
        fi
        ;;
      pathname)
        if [[ "$argc_url" == *"/"* && "$argc_url" != */ ]]; then
          path_part=$(echo "$argc_url" | sed -E 's/https?:\/\/[^\/]+\/([^\/]+).*/\1/')
          tool_name=$(echo "$path_part" | sed 's/-//g' | sed 's/^./\U&\E/')
        else
          tool_name=$(echo "$site_domain" | cut -d. -f1 | sed 's/^./\U&\E/')
        fi
        ;;
    esac
    
    echo ""
    echo "MCP関数: indexOf${tool_name} および getDocumentOf${tool_name}"
    echo "使用例: 'Claude DesktopのMCP設定に追加してください：'"
    echo "{"
    echo "  \"mcpServers\": {"
    echo "    \"${tool_name,,}\": {"
    echo "      \"command\": \"pnpm\","
    echo "      \"args\": ["
    echo "        \"dlx\","
    echo "        \"sitemcp\","
    echo "        \"$argc_url\""
    if [[ ${#argc_match[@]} -gt 0 ]]; then
      for pattern in "${argc_match[@]}"; do
        echo "        ,\"-m\","
        echo "        \"$pattern\""
      done
    fi
    if [[ -n "$argc_content_selector" ]]; then
      echo "        ,\"--content-selector\","
      echo "        \"$argc_content_selector\""
    fi
    echo "      ]"
    echo "    }"
    echo "  }"
    echo "}"
  fi
else
  echo "エラー: サイトデータの取得に失敗しました"
fi
