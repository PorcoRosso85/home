# Claude Permission Pipeline - 設計原理

## パイプライン構造

```
入力JSON → claude_config → 権限設定JSON → claude_sdk → Claude実行
```

## 変数と拡張ポイント

### 1. 入力JSON変数
```json
{
  "prompt": "${TASK_CONTENT}",
  "mode": "${PRESET_NAME}",     // config.ts内のプリセット名
  "workdir": "${WORK_DIR}",
  "env": {                       // 任意の環境変数
    "${KEY}": "${VALUE}"
  }
}
```

### 2. settings.json完全仕様
```json
{
  // API認証
  "apiKeyHelper": "${SCRIPT_PATH}",    // APIキー生成スクリプト
  
  // 履歴管理
  "cleanupPeriodDays": ${DAYS},        // デフォルト: 30
  
  // 環境変数
  "env": {
    "${VAR_NAME}": "${VALUE}"
  },
  
  // Git設定
  "includeCoAuthoredBy": ${BOOLEAN},   // デフォルト: true
  
  // 権限設定
  "permissions": {
    "allow": [
      "${TOOL_NAME}",                  // ツール名
      "${TOOL}(${CMD}:${PATTERN})"     // 例: "Bash(git:*)"
    ],
    "deny": [
      "${TOOL_NAME}",                  // 例: "WebFetch"
      "${TOOL}(${CMD}:*)"              // 例: "Bash(rm:*)"
    ],
    "additionalDirectories": [
      "${RELATIVE_PATH}"               // 例: "../docs/"
    ],
    "defaultMode": "${MODE}",          // "allowEdits" 等
    "disableBypassPermissionsMode": "${DISABLE_MODE}"
  },
  
  // フック設定
  "hooks": {
    // ツール実行前フック
    "PreToolUse": [{
      "matcher": "${REGEX_PATTERN}",   // ツール名の正規表現
      "hooks": [{
        "type": "command",
        "command": "${SHELL_COMMAND}"  // 実行するコマンド
      }]
    }],
    
    // ツール実行後フック
    "PostToolUse": [{
      "matcher": "${PATTERN}",
      "hooks": [{
        "type": "command",
        "command": "${CMD}"
      }]
    }],
    
    // 通知フック
    "Notification": [{
      "matcher": "",                   // 通常は空文字列
      "hooks": [{
        "type": "command",
        "command": "${NOTIFY_CMD}"
      }]
    }],
    
    // 終了時フック
    "Stop": [{
      "matcher": "",                   // 空文字列で全マッチ
      "hooks": [{
        "type": "command",
        "command": "${CLEANUP_CMD}"
      }]
    }]
  }
}
```

### 3. フック仕様詳細

#### フック実行フロー
```
1. PreToolUse → (ツール実行) → PostToolUse
2. Notification: 権限要求時・アイドル時
3. Stop: Claudeの応答終了時
```

#### フック入力（stdin経由のJSON）
```json
{
  // 共通フィールド
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  
  // PreToolUse/PostToolUse
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file",
    "content": "..."
  },
  
  // PostToolUseのみ
  "tool_response": {
    "filePath": "/path/to/file",
    "success": true
  },
  
  // Notification
  "message": "Task completed",
  "title": "Claude Code",
  
  // Stop
  "stop_hook_active": false
}
```

#### フック出力制御

**Exit Code方式:**
- `0`: 成功（stdoutは記録される）
- `2`: ブロック（PreToolUse: ツール実行中止、Stop: 終了中止）
- その他: エラー（実行は継続）

**JSON出力方式（高度な制御）:**
```json
{
  // 共通
  "continue": true,              // false=Claude停止
  "stopReason": "理由",          // continueがfalseの時表示
  "suppressOutput": false,       // stdout非表示
  
  // PreToolUse専用
  "decision": "approve|block",   // approve=権限チェック回避
  "reason": "判断理由",          // block時Claudeに表示
  
  // PostToolUse専用
  "decision": "block",           // Claudeに再考を促す
  "reason": "問題の説明",
  
  // Stop専用
  "decision": "block",           // 終了を阻止
  "reason": "継続理由"           // 必須
}
```

### 4. 実例：権限とフックの組み合わせ

#### ログ記録付き読み取り専用
```bash
echo '{
  "prompt": "コードレビュー",
  "mode": "readonly",
  "env": {
    "LOG_FILE": "/tmp/review.log"
  }
}' | claude_config
# → settings.jsonにフック追加:
#    "PreToolUse": [{"command": "echo $(date) $TOOL >> $LOG_FILE"}]
```

#### Git操作のみ許可
```bash
echo '{
  "prompt": "ブランチ管理",
  "mode": "custom",
  "env": {
    "ALLOWED_PATTERNS": "Bash(git:*),Read,LS"
  }
}' | claude_config
```

#### 危険コマンドブロック＋通知
```bash
echo '{
  "prompt": "本番作業",
  "mode": "production",
  "env": {
    "NOTIFY_WEBHOOK": "https://hooks.slack.com/..."
  }
}' | claude_config
# → PreToolUseフックで危険コマンドを検知して通知
```

#### タイムアウト付き実行
```bash
echo '{
  "prompt": "重い処理",
  "mode": "development",
  "env": {
    "MAX_DURATION": "300"
  }
}' | claude_config
# → PostToolUseフックでタイマーチェック
```

## 拡張方法

### 新しいプリセット追加
```typescript
// config.ts内のPRESETSに追加
"custom-preset": {
  allowedTools: ["${TOOL1}", "${TOOL2}"],
  settings: {
    permissions: {
      allow: ["${PATTERN1}"],
      deny: ["${PATTERN2}"]
    }
  }
}
```

### 動的な権限設定
```bash
# 環境変数で制御
ALLOWED_TOOLS="${TOOLS}" jq -n '{
  prompt: env.PROMPT,
  mode: "custom",
  env: { allowedTools: env.ALLOWED_TOOLS }
}' | claude_config | claude_sdk
```

### 条件付き権限
```bash
# パイプライン前段で権限を計算
PERMISSIONS=$(analyze_task "$TASK")
echo "{...permissions: $PERMISSIONS}" | pipeline
```

## 設計思想
- プリセットは出発点、カスタマイズ可能
- JSONによる宣言的設定
- パイプラインの各段階で変換・拡張可能
- 環境変数による動的制御

## 高度な使用例

### 完全なフック実装例

#### Bashコマンド検証フック
```python
#!/usr/bin/env python3
import json
import sys
import re

# 標準入力からJSON読み込み
data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
command = data.get("tool_input", {}).get("command", "")

# Bashツール以外は通過
if tool_name != "Bash":
    sys.exit(0)

# 危険コマンドパターン
DANGEROUS = [
    (r'\brm\s+-rf\s+/', "rm -rf / は危険です"),
    (r'\bdd\s+.*of=/dev/[sh]d', "ディスクへの直接書き込みは禁止"),
    (r'>\s*/etc/', "/etcへの書き込みは禁止"),
]

# 検証
for pattern, msg in DANGEROUS:
    if re.search(pattern, command):
        # JSON出力でブロック
        print(json.dumps({
            "decision": "block",
            "reason": msg
        }))
        sys.exit(0)

# 承認
sys.exit(0)
```

#### 自動フォーマットフック
```bash
#!/bin/bash
# PostToolUse: ファイル編集後の自動フォーマット
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r .tool_name)
FILE_PATH=$(echo "$INPUT" | jq -r .tool_input.file_path)

# ファイル編集ツール以外は無視
if [[ ! "$TOOL_NAME" =~ ^(Write|Edit|MultiEdit)$ ]]; then
    exit 0
fi

# 拡張子に応じてフォーマッタ実行
case "$FILE_PATH" in
    *.py) ruff format "$FILE_PATH" ;;
    *.js|*.ts) prettier --write "$FILE_PATH" ;;
    *.go) gofmt -w "$FILE_PATH" ;;
    *.rs) rustfmt "$FILE_PATH" ;;
esac

# 成功メッセージ（記録される）
echo "Formatted: $FILE_PATH"
```

### 監査ログ付き権限管理
```bash
# フック付き設定生成
cat <<'EOF' > /tmp/audit-hook.sh
#!/bin/bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r .tool_name)
TOOL_INPUT=$(echo "$INPUT" | jq -c .tool_input)
SESSION_ID=$(echo "$INPUT" | jq -r .session_id)

# 監査ログ記録
echo "[$(date -Iseconds)] $SESSION_ID: $TOOL_NAME $TOOL_INPUT" >> /var/log/claude-audit.log

# Webhook通知（重要操作のみ）
if [[ "$TOOL_NAME" =~ ^(Write|Bash|MultiEdit)$ ]]; then
    curl -s -X POST "$AUDIT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"session\": \"$SESSION_ID\", \"tool\": \"$TOOL_NAME\", \"input\": $TOOL_INPUT}"
fi
EOF

chmod +x /tmp/audit-hook.sh

# 設定適用
echo '{
  "prompt": "本番環境作業",
  "mode": "production"
}' | claude_config | \
jq '.settings.hooks.PreToolUse = [{
  matcher: ".*",
  hooks: [{type: "command", command: "/tmp/audit-hook.sh"}]
}]' > /tmp/config.json

cat /tmp/config.json | claude_sdk
```

### 時間帯別権限制御
```bash
HOUR=$(date +%H)
if [ $HOUR -ge 9 -a $HOUR -lt 18 ]; then
  MODE="development"
else
  MODE="readonly"  # 業務時間外は読み取り専用
fi

echo "{\"prompt\": \"$1\", \"mode\": \"$MODE\"}" | pipeline
```

### プロジェクト別設定の自動適用
```bash
# プロジェクトルートの.claude-config.jsonを読み込み
PROJECT_CONFIG=$(find . -name ".claude-config.json" -exec cat {} \; | head -1)
BASE_CONFIG="{\"prompt\": \"$TASK\", \"workdir\": \"$(pwd)\"}"

# プロジェクト設定とマージ
echo "$BASE_CONFIG" | jq ". + $PROJECT_CONFIG" | claude_config | claude_sdk
```