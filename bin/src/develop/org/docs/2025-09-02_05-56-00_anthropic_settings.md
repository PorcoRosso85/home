[Anthropic home page light logo dark logo](/)

設定

Claude Code設定

[ようこそ](/ja/home) [開発者プラットフォーム](/ja/docs/intro) [Claude コード](/ja/docs/claude-code/overview) [Model Context Protocol (MCP)](/en/docs/mcp) [APIリファレンス](/en/api/messages) [リソース](/ja/resources/overview) [リリースノート](/ja/release-notes/overview)

##### はじめに

- [概要](/ja/docs/claude-code/overview)
- [クイックスタート](/ja/docs/claude-code/quickstart)
- [一般的なワークフロー](/ja/docs/claude-code/common-workflows)

##### Claude Codeで構築

- [サブエージェント](/ja/docs/claude-code/sub-agents)
- [出力スタイル](/ja/docs/claude-code/output-styles)
- [Claude Code フック](/ja/docs/claude-code/hooks-guide)
- [GitHub Actions](/ja/docs/claude-code/github-actions)
- [Model Context Protocol (MCP)](/ja/docs/claude-code/mcp)
- [トラブルシューティング](/ja/docs/claude-code/troubleshooting)

##### Claude Code SDK

- [概要](/ja/docs/claude-code/sdk/sdk-overview)
- [ヘッドレスモード](/ja/docs/claude-code/sdk/sdk-headless)
- [Python](/ja/docs/claude-code/sdk/sdk-python)
- [TypeScript](/ja/docs/claude-code/sdk/sdk-typescript)

##### デプロイメント

- [概要](/ja/docs/claude-code/third-party-integrations)
- [Amazon Bedrock](/ja/docs/claude-code/amazon-bedrock)
- [Google Vertex AI](/ja/docs/claude-code/google-vertex-ai)
- [Corporate proxy](/ja/docs/claude-code/corporate-proxy)
- [LLMゲートウェイ](/ja/docs/claude-code/llm-gateway)
- [開発コンテナ](/ja/docs/claude-code/devcontainer)

##### 管理

- [高度なインストール](/ja/docs/claude-code/setup)
- [アイデンティティとアクセス管理](/ja/docs/claude-code/iam)
- [セキュリティ](/ja/docs/claude-code/security)
- [データ使用](/ja/docs/claude-code/data-usage)
- [監視](/ja/docs/claude-code/monitoring-usage)
- [コスト](/ja/docs/claude-code/costs)
- [アナリティクス](/ja/docs/claude-code/analytics)

##### 設定

- [設定](/ja/docs/claude-code/settings)
- [IDEにClaude Codeを追加する](/ja/docs/claude-code/ide-integrations)
- [ターミナル設定](/ja/docs/claude-code/terminal-config)
- [メモリ管理](/ja/docs/claude-code/memory)
- [ステータスライン設定](/ja/docs/claude-code/statusline)

##### リファレンス

- [CLIリファレンス](/ja/docs/claude-code/cli-reference)
- [インタラクティブモード](/ja/docs/claude-code/interactive-mode)
- [スラッシュコマンド](/ja/docs/claude-code/slash-commands)
- [フックリファレンス](/ja/docs/claude-code/hooks)

##### リソース

- [法的事項とコンプライアンス](/ja/docs/claude-code/legal-and-compliance)

Claude Codeは、あなたのニーズに合わせて動作を設定するための様々な設定を提供しています。インタラクティブREPLを使用する際に `/config` コマンドを実行することで、Claude Codeを設定できます。

## [​](#%E8%A8%AD%E5%AE%9A%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB)

設定ファイル

`settings.json` ファイルは、階層設定を通じてClaude Codeを設定するための公式メカニズムです：

- **ユーザー設定** は `~/.claude/settings.json` で定義され、すべてのプロジェクトに適用されます。
- **プロジェクト設定** はプロジェクトディレクトリに保存されます：
  - `.claude/settings.json` はソース管理にチェックインされ、チームと共有される設定用
  - `.claude/settings.local.json` はチェックインされない設定用で、個人の設定や実験に便利です。Claude Codeは作成時に `.claude/settings.local.json` を無視するようにgitを設定します。
- Claude Codeのエンタープライズデプロイメントでは、 **エンタープライズ管理ポリシー設定** もサポートしています。これらはユーザーおよびプロジェクト設定よりも優先されます。システム管理者は以下にポリシーをデプロイできます：
  - macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
  - LinuxおよびWSL: `/etc/claude-code/managed-settings.json`
  - Windows: `C:\ProgramData\ClaudeCode\managed-settings.json`

Example settings.json

```JSON
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  }
}
```

### [​](#%E5%88%A9%E7%94%A8%E5%8F%AF%E8%83%BD%E3%81%AA%E8%A8%AD%E5%AE%9A)

利用可能な設定

`settings.json` は多数のオプションをサポートしています：

| キー | 説明 | 例 |
| --- | --- | --- |
| `apiKeyHelper` | 認証値を生成するために `/bin/sh` で実行されるカスタムスクリプト。この値はモデルリクエストの `X-Api-Key` および `Authorization: Bearer` ヘッダーとして送信されます | `/bin/generate_temp_api_key.sh` |
| `cleanupPeriodDays` | 最後のアクティビティ日に基づいてチャットトランスクリプトをローカルに保持する期間（デフォルト：30日） | `20` |
| `env` | すべてのセッションに適用される環境変数 | `{ " FOO ": " bar " }` |
| `includeCoAuthoredBy` | gitコミットとプルリクエストに `co-authored-by Claude` 署名を含めるかどうか（デフォルト： `true` ） | `false` |
| `permissions` | 権限の構造については下の表を参照してください。 |  |
| `hooks` | ツール実行の前後に実行するカスタムコマンドを設定します。 [hooksドキュメント](hooks) を参照 | `{ " PreToolUse ": { " Bash ": " echo ' Running command... ' " }}` |
| `model` | Claude Codeで使用するデフォルトモデルをオーバーライド | `" claude-3-5-sonnet-20241022 "` |
| `statusLine` | コンテキストを表示するカスタムステータスラインを設定します。 [statusLineドキュメント](statusline) を参照 | `{ " type ": " command ", " command ": " ~/.claude/statusline.sh " }` |
| `forceLoginMethod` | `claudeai` を使用してClaude.aiアカウントへのログインを制限、 `console` を使用してAnthropic Console（API使用料金）アカウントへのログインを制限 | `claudeai` |
| `forceLoginOrgUUID` | ログイン時に自動的に選択する組織のUUIDを指定し、組織選択ステップをバイパスします。 `forceLoginMethod` の設定が必要 | `" xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx "` |
| `enableAllProjectMcpServers` | プロジェクトの `.mcp.json` ファイルで定義されたすべてのMCPサーバーを自動的に承認 | `true` |
| `enabledMcpjsonServers` | `.mcp.json` ファイルから承認する特定のMCPサーバーのリスト | `[ " memory ", " github " ]` |
| `disabledMcpjsonServers` | `.mcp.json` ファイルから拒否する特定のMCPサーバーのリスト | `[ " filesystem " ]` |
| `awsAuthRefresh` | `.aws` ディレクトリを変更するカスタムスクリプト（ [高度な認証情報設定](/ja/docs/claude-code/amazon-bedrock#advanced-credential-configuration) を参照） | `aws sso login --profile myprofile` |
| `awsCredentialExport` | AWS認証情報を含むJSONを出力するカスタムスクリプト（ [高度な認証情報設定](/ja/docs/claude-code/amazon-bedrock#advanced-credential-configuration) を参照） | `/bin/generate_aws_grant.sh` |

### [​](#%E6%A8%A9%E9%99%90%E8%A8%AD%E5%AE%9A)

権限設定

| キー | 説明 | 例 |
| --- | --- | --- |
| `allow` | ツール使用を許可する [権限ルール](/ja/docs/claude-code/iam#configuring-permissions) の配列 | `[ " Bash(git diff:*) " ]` |
| `ask` | ツール使用時に確認を求める [権限ルール](/ja/docs/claude-code/iam#configuring-permissions) の配列。 | `[ " Bash(git push:*) " ]` |
| `deny` | ツール使用を拒否する [権限ルール](/ja/docs/claude-code/iam#configuring-permissions) の配列。これを使用してClaude Codeアクセスから機密ファイルを除外することもできます。 | `[ " WebFetch ", " Bash(curl:*) ", " Read(./.env) ", " Read(./secrets/**) " ]` |
| `additionalDirectories` | Claudeがアクセスできる追加の [作業ディレクトリ](iam#working-directories) | `[ "../docs/ " ]` |
| `defaultMode` | Claude Code起動時のデフォルト [権限モード](iam#permission-modes) | `" acceptEdits "` |
| `disableBypassPermissionsMode` | `" disable "` に設定すると `bypassPermissions` モードの有効化を防ぎます。 [管理ポリシー設定](iam#enterprise-managed-policy-settings) を参照 | `" disable "` |

### [​](#%E8%A8%AD%E5%AE%9A%E3%81%AE%E5%84%AA%E5%85%88%E9%A0%86%E4%BD%8D)

設定の優先順位

設定は優先順位の順序で適用されます（高い順から低い順）：

1. **エンタープライズ管理ポリシー** （ `managed-settings.json` ）
  - IT/DevOpsによってデプロイ
  - オーバーライドできません
1. **コマンドライン引数**
  - 特定のセッションの一時的なオーバーライド
1. **ローカルプロジェクト設定** （ `.claude/settings.local.json` ）
  - 個人のプロジェクト固有設定
1. **共有プロジェクト設定** （ `.claude/settings.json` ）
  - ソース管理でのチーム共有プロジェクト設定
1. **ユーザー設定** （ `~/.claude/settings.json` ）
  - 個人のグローバル設定

この階層により、エンタープライズセキュリティポリシーが常に適用される一方で、チームや個人が体験をカスタマイズできます。

### [​](#%E8%A8%AD%E5%AE%9A%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%81%AE%E9%87%8D%E8%A6%81%E3%81%AA%E3%83%9D%E3%82%A4%E3%83%B3%E3%83%88)

設定システムの重要なポイント

- **メモリファイル（CLAUDE.md）** ：Claudeが起動時に読み込む指示とコンテキストを含む
- **設定ファイル（JSON）** ：権限、環境変数、ツールの動作を設定
- **スラッシュコマンド** ：セッション中に `/command-name` で呼び出せるカスタムコマンド
- **MCPサーバー** ：追加のツールと統合でClaude Codeを拡張
- **優先順位** ：上位レベルの設定（エンタープライズ）が下位レベル（ユーザー/プロジェクト）をオーバーライド
- **継承** ：設定はマージされ、より具体的な設定がより広範な設定に追加またはオーバーライド

### [​](#%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%83%97%E3%83%AD%E3%83%B3%E3%83%97%E3%83%88%E3%81%AE%E5%8F%AF%E7%94%A8%E6%80%A7)

システムプロンプトの可用性

claude.aiとは異なり、このウェブサイトではClaude Codeの内部システムプロンプトを公開していません。Claude Codeの動作にカスタム指示を追加するには、CLAUDE.mdファイルまたは `--append-system-prompt` を使用してください。

### [​](#%E6%A9%9F%E5%AF%86%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%81%AE%E9%99%A4%E5%A4%96)

機密ファイルの除外

Claude Codeが機密情報を含むファイル（APIキー、シークレット、環境ファイルなど）にアクセスするのを防ぐには、 `.claude/settings.json` ファイルの `permissions.deny` 設定を使用します：

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "Read(./build)"
    ]
  }
}
```

これは非推奨の `ignorePatterns` 設定を置き換えます。これらのパターンに一致するファイルはClaude Codeから完全に見えなくなり、機密データの偶発的な露出を防ぎます。

## [​](#%E3%82%B5%E3%83%96%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E8%A8%AD%E5%AE%9A)

サブエージェント設定

Claude Codeは、ユーザーレベルとプロジェクトレベルの両方で設定できるカスタムAIサブエージェントをサポートしています。これらのサブエージェントはYAMLフロントマターを持つMarkdownファイルとして保存されます：

- **ユーザーサブエージェント** ： `~/.claude/agents/` - すべてのプロジェクトで利用可能
- **プロジェクトサブエージェント** ： `.claude/agents/` - プロジェクト固有でチームと共有可能

サブエージェントファイルは、カスタムプロンプトとツール権限を持つ専門化されたAIアシスタントを定義します。サブエージェントの作成と使用について詳しくは、 [サブエージェントドキュメント](/ja/docs/claude-code/sub-agents) をご覧ください。

## [​](#%E7%92%B0%E5%A2%83%E5%A4%89%E6%95%B0)

環境変数

Claude Codeは、その動作を制御するために以下の環境変数をサポートしています：

すべての環境変数は [`settings.json`](/_sites/docs.anthropic.com/ja/docs/claude-code/settings#available-settings) でも設定できます。これは各セッションで環境変数を自動的に設定したり、チーム全体や組織全体に環境変数のセットを展開したりする方法として便利です。

| 変数 | 目的 |
| --- | --- |
| `ANTHROPIC_API_KEY` | `X-Api-Key` ヘッダーとして送信されるAPIキー、通常はClaude SDK用（インタラクティブ使用の場合は `/login` を実行） |
| `ANTHROPIC_AUTH_TOKEN` | `Authorization` ヘッダーのカスタム値（ここで設定した値は `Bearer ` で前置されます） |
| `ANTHROPIC_CUSTOM_HEADERS` | リクエストに追加したいカスタムヘッダー（ `Name: Value` 形式） |
| `ANTHROPIC_MODEL` | 使用するカスタムモデルの名前（ [モデル設定](/ja/docs/claude-code/bedrock-vertex-proxies#model-configuration) を参照） |
| `ANTHROPIC_SMALL_FAST_MODEL` | [バックグラウンドタスク用のHaikuクラスモデル](/ja/docs/claude-code/costs) |
| `ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION` | Bedrockを使用する際の小型/高速モデルのAWSリージョンをオーバーライド |
| `AWS_BEARER_TOKEN_BEDROCK` | 認証用のBedrock APIキー（ [Bedrock APIキー](https://aws.amazon.com/blogs/machine-learning/accelerate-ai-development-with-amazon-bedrock-api-keys/) を参照） |
| `BASH_DEFAULT_TIMEOUT_MS` | 長時間実行されるbashコマンドのデフォルトタイムアウト |
| `BASH_MAX_TIMEOUT_MS` | モデルが長時間実行されるbashコマンドに設定できる最大タイムアウト |
| `BASH_MAX_OUTPUT_LENGTH` | bash出力が中央で切り詰められる前の最大文字数 |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | 各Bashコマンド後に元の作業ディレクトリに戻る |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` | 認証情報を更新する間隔（ミリ秒）（ `apiKeyHelper` 使用時） |
| `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL` | IDE拡張機能の自動インストールをスキップ |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | ほとんどのリクエストの最大出力トークン数を設定 |
| `CLAUDE_CODE_USE_BEDROCK` | [Bedrock](/ja/docs/claude-code/amazon-bedrock) を使用 |
| `CLAUDE_CODE_USE_VERTEX` | [Vertex](/ja/docs/claude-code/google-vertex-ai) を使用 |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH` | Bedrockの AWS認証をスキップ（LLMゲートウェイ使用時など） |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH` | VertexのGoogle認証をスキップ（LLMゲートウェイ使用時など） |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `DISABLE_AUTOUPDATER` 、 `DISABLE_BUG_COMMAND` 、 `DISABLE_ERROR_REPORTING` 、 `DISABLE_TELEMETRY` の設定と同等 |
| `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` | 会話コンテキストに基づく自動ターミナルタイトル更新を無効にするには `1` に設定 |
| `DISABLE_AUTOUPDATER` | 自動更新を無効にするには `1` に設定。これは `autoUpdates` 設定よりも優先されます。 |
| `DISABLE_BUG_COMMAND` | `/bug` コマンドを無効にするには `1` に設定 |
| `DISABLE_COST_WARNINGS` | コスト警告メッセージを無効にするには `1` に設定 |
| `DISABLE_ERROR_REPORTING` | Sentryエラーレポートをオプトアウトするには `1` に設定 |
| `DISABLE_NON_ESSENTIAL_MODEL_CALLS` | フレーバーテキストなどの非重要パスのモデル呼び出しを無効にするには `1` に設定 |
| `DISABLE_TELEMETRY` | Statsigテレメトリをオプトアウトするには `1` に設定（Statsigイベントにはコード、ファイルパス、bashコマンドなどのユーザーデータは含まれません） |
| `HTTP_PROXY` | ネットワーク接続用のHTTPプロキシサーバーを指定 |
| `HTTPS_PROXY` | ネットワーク接続用のHTTPSプロキシサーバーを指定 |
| `MAX_THINKING_TOKENS` | モデルの思考予算を強制 |
| `MCP_TIMEOUT` | MCPサーバー起動のタイムアウト（ミリ秒） |
| `MCP_TOOL_TIMEOUT` | MCPツール実行のタイムアウト（ミリ秒） |
| `MAX_MCP_OUTPUT_TOKENS` | MCPツールレスポンスで許可される最大トークン数。Claude Codeは出力が10,000トークンを超えると警告を表示します（デフォルト：25000） |
| `USE_BUILTIN_RIPGREP` | Claude Codeに含まれる `rg` の代わりにシステムインストールされた `rg` を使用するには `0` に設定 |
| `VERTEX_REGION_CLAUDE_3_5_HAIKU` | Vertex AI使用時のClaude 3.5 Haikuのリージョンをオーバーライド |
| `VERTEX_REGION_CLAUDE_3_5_SONNET` | Vertex AI使用時のClaude Sonnet 3.5のリージョンをオーバーライド |
| `VERTEX_REGION_CLAUDE_3_7_SONNET` | Vertex AI使用時のClaude 3.7 Sonnetのリージョンをオーバーライド |
| `VERTEX_REGION_CLAUDE_4_0_OPUS` | Vertex AI使用時のClaude 4.0 Opusのリージョンをオーバーライド |
| `VERTEX_REGION_CLAUDE_4_0_SONNET` | Vertex AI使用時のClaude 4.0 Sonnetのリージョンをオーバーライド |
| `VERTEX_REGION_CLAUDE_4_1_OPUS` | Vertex AI使用時のClaude 4.1 Opusのリージョンをオーバーライド |

## [​](#%E8%A8%AD%E5%AE%9A%E3%82%AA%E3%83%97%E3%82%B7%E3%83%A7%E3%83%B3)

設定オプション

設定を管理するには、以下のコマンドを使用します：

- 設定一覧： `claude config list`
- 設定確認： `claude config get < key >`
- 設定変更： `claude config set < key > < value >`
- 設定への追加（リスト用）： `claude config add < key > < value >`
- 設定からの削除（リスト用）： `claude config remove < key > < value >`

デフォルトでは `config` はプロジェクト設定を変更します。グローバル設定を管理するには、 `--global` （または `-g` ）フラグを使用します。

### [​](#%E3%82%B0%E3%83%AD%E3%83%BC%E3%83%90%E3%83%AB%E8%A8%AD%E5%AE%9A)

グローバル設定

グローバル設定を設定するには、 `claude config set -g < key > < value >` を使用します：

| キー | 説明 | 例 |
| --- | --- | --- |
| `autoUpdates` | 自動更新を有効にするかどうか（デフォルト： `true` ）。有効にすると、Claude Codeはバックグラウンドで自動的に更新をダウンロードしてインストールします。更新はClaude Codeを再起動すると適用されます。 | `false` |
| `preferredNotifChannel` | 通知を受け取りたい場所（デフォルト： `iterm2` ） | `iterm2` 、 `iterm2_with_bell` 、 `terminal_bell` 、または `notifications_disabled` |
| `theme` | カラーテーマ | `dark` 、 `light` 、 `light-daltonized` 、または `dark-daltonized` |
| `verbose` | 完全なbashおよびコマンド出力を表示するかどうか（デフォルト： `false` ） | `true` |

## [​](#claude%E3%81%8C%E5%88%A9%E7%94%A8%E3%81%A7%E3%81%8D%E3%82%8B%E3%83%84%E3%83%BC%E3%83%AB)

Claudeが利用できるツール

Claude Codeは、コードベースを理解し変更するのに役立つ強力なツールセットにアクセスできます：

| ツール | 説明 | 権限が必要 |
| --- | --- | --- |
| **Bash** | 環境でシェルコマンドを実行 | はい |
| **Edit** | 特定のファイルに対象を絞った編集を行う | はい |
| **Glob** | パターンマッチングに基づいてファイルを検索 | いいえ |
| **Grep** | ファイル内容でパターンを検索 | いいえ |
| **LS** | ファイルとディレクトリを一覧表示 | いいえ |
| **MultiEdit** | 単一ファイルに対して複数の編集をアトミックに実行 | はい |
| **NotebookEdit** | Jupyterノートブックセルを変更 | はい |
| **NotebookRead** | Jupyterノートブックの内容を読み取り表示 | いいえ |
| **Read** | ファイルの内容を読み取り | いいえ |
| **Task** | 複雑な多段階タスクを処理するサブエージェントを実行 | いいえ |
| **TodoWrite** | 構造化されたタスクリストを作成・管理 | いいえ |
| **WebFetch** | 指定されたURLからコンテンツを取得 | はい |
| **WebSearch** | ドメインフィルタリングでウェブ検索を実行 | はい |
| **Write** | ファイルを作成または上書き | はい |

権限ルールは `/allowed-tools` または [権限設定](/ja/docs/claude-code/settings#available-settings) で設定できます。

### [​](#%E3%83%95%E3%83%83%E3%82%AF%E3%81%A7%E3%83%84%E3%83%BC%E3%83%AB%E3%82%92%E6%8B%A1%E5%BC%B5)

フックでツールを拡張

[Claude Codeフック](/ja/docs/claude-code/hooks-guide) を使用して、任意のツール実行の前後にカスタムコマンドを実行できます。

例えば、ClaudeがPythonファイルを変更した後に自動的にPythonフォーマッターを実行したり、特定のパスへのWrite操作をブロックして本番設定ファイルの変更を防いだりできます。

## [​](#%E9%96%A2%E9%80%A3%E9%A0%85%E7%9B%AE)

関連項目

- [アイデンティティとアクセス管理](/ja/docs/claude-code/iam#configuring-permissions) - Claude Codeの権限システムについて学ぶ
- [IAMとアクセス制御](/ja/docs/claude-code/iam#enterprise-managed-policy-settings) - エンタープライズポリシー管理
- [トラブルシューティング](/ja/docs/claude-code/troubleshooting#auto-updater-issues) - 一般的な設定問題の解決策

Was this page helpful?

[アナリティクス](/ja/docs/claude-code/analytics) [IDEにClaude Codeを追加する](/ja/docs/claude-code/ide-integrations)

On this page

- [設定ファイル](#%E8%A8%AD%E5%AE%9A%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB)
- [利用可能な設定](#%E5%88%A9%E7%94%A8%E5%8F%AF%E8%83%BD%E3%81%AA%E8%A8%AD%E5%AE%9A)
- [権限設定](#%E6%A8%A9%E9%99%90%E8%A8%AD%E5%AE%9A)
- [設定の優先順位](#%E8%A8%AD%E5%AE%9A%E3%81%AE%E5%84%AA%E5%85%88%E9%A0%86%E4%BD%8D)
- [設定システムの重要なポイント](#%E8%A8%AD%E5%AE%9A%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%81%AE%E9%87%8D%E8%A6%81%E3%81%AA%E3%83%9D%E3%82%A4%E3%83%B3%E3%83%88)
- [システムプロンプトの可用性](#%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%83%97%E3%83%AD%E3%83%B3%E3%83%97%E3%83%88%E3%81%AE%E5%8F%AF%E7%94%A8%E6%80%A7)
- [機密ファイルの除外](#%E6%A9%9F%E5%AF%86%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%81%AE%E9%99%A4%E5%A4%96)
- [サブエージェント設定](#%E3%82%B5%E3%83%96%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E8%A8%AD%E5%AE%9A)
- [環境変数](#%E7%92%B0%E5%A2%83%E5%A4%89%E6%95%B0)
- [設定オプション](#%E8%A8%AD%E5%AE%9A%E3%82%AA%E3%83%97%E3%82%B7%E3%83%A7%E3%83%B3)
- [グローバル設定](#%E3%82%B0%E3%83%AD%E3%83%BC%E3%83%90%E3%83%AB%E8%A8%AD%E5%AE%9A)
- [Claudeが利用できるツール](#claude%E3%81%8C%E5%88%A9%E7%94%A8%E3%81%A7%E3%81%8D%E3%82%8B%E3%83%84%E3%83%BC%E3%83%AB)
- [フックでツールを拡張](#%E3%83%95%E3%83%83%E3%82%AF%E3%81%A7%E3%83%84%E3%83%BC%E3%83%AB%E3%82%92%E6%8B%A1%E5%BC%B5)
- [関連項目](#%E9%96%A2%E9%80%A3%E9%A0%85%E7%9B%AE)
