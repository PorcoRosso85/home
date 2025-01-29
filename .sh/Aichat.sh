#!/bin/bash
alias aichat='aichat --prompt "あなたはソフトウェアのエキスパートであり英語で思考し 日本語で回答する、特に指定がないときには端的に回答して"'

# # Client-Related Envs
# export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # OpenAIのAPIキー
# export GEMINI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"     # GeminiのAPIキー
# export AICHAT_PLATFORM="openai"                              # 使用するAIプラットフォーム（設定ファイルがない場合に使用）

# # API設定のパッチ
# export AICHAT_PATCH_OPENAI_CHAT_COMPLETIONS='{"gpt-4o":{"body":{"seed":666,"temperature":0}}}' # OpenAI APIリクエストのカスタマイズ

# # シェル設定
# export AICHAT_SHELL="/bin/bash"  # 使用するシェルを指定（自動検出をオーバーライド）

# ファイル/ディレクトリ設定
export AICHAT_CONFIG_DIR="$HOME/.config/aichat"              # 設定ディレクトリのカスタマイズ
export AICHAT_ENV_FILE="$HOME/.aichat.env"                   # .envファイルの場所をカスタマイズ
export AICHAT_CONFIG_FILE="$HOME/.config/aichat/config.yaml" # config.yamlファイルの場所をカスタマイズ
export AICHAT_ROLES_DIR="$HOME/.config/aichat/roles"         # ロールディレクトリの場所をカスタマイズ
export AICHAT_SESSIONS_DIR="$HOME/.config/aichat/sessions"   # セッションディレクトリの場所をカスタマイズ
export AICHAT_RAGS_DIR="$HOME/.config/aichat/rags"           # RAGディレクトリの場所をカスタマイズ
export AICHAT_FUNCTIONS_DIR="$HOME/.config/aichat/functions" # 関数ディレクトリの場所をカスタマイズ
export AICHAT_MESSAGES_FILE="$HOME/.config/aichat/messages.md" # メッセージファイルの場所をカスタマイズ

# エージェント関連の設定
export CODER_FUNCTIONS_DIR="$HOME/.config/aichat/coder_functions" # CODERエージェントの関数ディレクトリをカスタマイズ
export CODER_DATA_DIR="$HOME/.config/aichat/coder_data"           # CODERエージェントのデータディレクトリをカスタマイズ

# ロギング設定
export AICHAT_LOG_LEVEL="debug"                              # デバッグログを有効化
export AICHAT_LOG_FILE="$HOME/.config/aichat/aichat.log"     # ログファイルの場所をカスタマイズ

# 一般的な設定
# export HTTPS_PROXY="http://proxy.example.com:8080"           # HTTPSプロキシを指定
# export ALL_PROXY="socks5://proxy.example.com:1080"           # すべてのプロトコルに対するプロキシを指定
# export NO_COLOR="1"                                          # カラー出力を無効化
# export EDITOR="vim"                                          # デフォルトエディタを指定
# export XDG_CONFIG_HOME="$HOME/.config"                       # 設定ディレクトリの場所を指定
