# GitHub Actions Self-hosted Runner テスト計画書

## テスト計画書

### 前提条件

#### 必須要件
1. **環境要件**
   - Nix環境が利用可能であること
   - Dockerデーモンが起動していること
   - インターネット接続が可能であること
   - GitHubアカウントとリポジトリへのアクセス権限

2. **認証要件**
   - GitHub CLIがインストールされていること (`gh`)
   - GitHubへの認証が完了していること (`gh auth login`)
   - リポジトリのActions設定で必要な権限が付与されていること

3. **リポジトリ要件**
   - リポジトリルートに`.github/workflows/`ディレクトリが存在すること
   - テスト用ワークフローファイルが配置可能であること
   - Self-hosted runnerの登録が許可されていること

4. **事前準備**
   ```bash
   nix develop
   gh auth status
   ```

### テストケース

#### 優先度: 高（P1）- 基本機能テスト

| ID | テストケース | 期待結果 | 依存関係 |
|----|------------|---------|---------|
| T01 | Runner登録テスト | Runnerが正常に登録され、GitHubコンソールに表示される | なし |
| T02 | Runner接続性確認 | Runnerのステータスが"online"となる | T01 |
| T03 | 手動ワークフロー実行 | workflow_dispatchで起動したジョブが正常に完了する | T02 |
| T04 | Runnerクリーンアップ | Runnerの登録解除と関連ファイルの削除が完了する | T01 |

#### 優先度: 中（P2）- トリガーテスト

| ID | テストケース | 期待結果 | 依存関係 |
|----|------------|---------|---------|
| T05 | Push イベントトリガー | ファイル変更のpushでワークフローが起動する | T02 |
| T06 | Pull Request トリガー | PR作成時にワークフローが起動する | T02 |
| T07 | ワークフロー完了待機 | 実行中のワークフローの完了を検知できる | T03 |
| T08 | ジョブステータス確認 | 特定ジョブの成功/失敗を正しく判定できる | T03 |

#### 優先度: 低（P3）- 高度な検証テスト

| ID | テストケース | 期待結果 | 依存関係 |
|----|------------|---------|---------|
| T09 | ログ内容検証 | 指定したパターンがログに含まれることを確認できる | T03 |
| T10 | アーティファクト確認 | ワークフローで生成されたアーティファクトを取得できる | T03 |
| T11 | 意図的な失敗テスト | exit 1で失敗するジョブが正しく失敗として記録される | T03 |
| T12 | continue-on-errorテスト | エラーが発生してもワークフローが継続する | T03 |
| T13 | パフォーマンステスト | 簡単なジョブが30秒以内に完了する | T03 |

### 実行手順

#### Phase 1: 環境準備（5分）
```bash
# 1. 開発環境に入る
cd /home/nixos/bin/src/poc/gha-self
nix develop

# 2. GitHub認証確認
gh auth status
gh repo view --json nameWithOwner

# 3. 必要なワークフローファイルの確認
ls -la /home/nixos/bin/.github/workflows/
```

#### Phase 2: 基本機能テスト（10分）
```bash
# T01: Runner登録
TOKEN=$(gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runners/registration-token \
  -q .token)

github-runner configure \
  --url "https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)" \
  --token "$TOKEN" \
  --name "test-runner-$(date +%s)" \
  --labels "self-hosted,test,ephemeral" \
  --work "_work_test" \
  --unattended \
  --ephemeral

# T02: 接続性確認
gh api /repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runners \
  | jq '.runners[] | {name, status}'

# T03: 手動実行テスト
github-runner run --once &
RUNNER_PID=$!
gh workflow run self-hosted-cowsay-test.yml
sleep 10
wait $RUNNER_PID
```

#### Phase 3: トリガーテスト（15分）
```bash
# T05: Push トリガーテスト
git checkout -b test-runner-$(date +%s)
echo "test" > test.txt
git add test.txt
git commit -m "test: trigger runner"
git push origin HEAD

# T06: PR トリガーテスト（オプション）
gh pr create --title "Test PR" --body "Testing runner"

# T07-T08: ステータス確認
RUN_ID=$(gh run list --limit 1 --json databaseId -q '.[0].databaseId')
gh run view "$RUN_ID" --json status,conclusion
```

#### Phase 4: クリーンアップ（5分）
```bash
# T04: クリーンアップ
pkill -f github-runner || true

REMOVE_TOKEN=$(gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runners/remove-token \
  -q .token)

github-runner remove --token "$REMOVE_TOKEN"

# テストブランチの削除
git checkout main
git branch -D test-runner-*
git push origin --delete test-runner-*

# ファイルクリーンアップ
rm -rf _work_test _diag_test
```

### リスクと対策

#### リスク1: Runner登録の失敗
- **原因**: トークンの有効期限切れ、権限不足
- **対策**: 
  - トークンは取得後すぐに使用する（1時間で失効）
  - リポジトリのSettings > Actions > Runnersで権限を確認
  - エラーログを`_diag/`ディレクトリで確認

#### リスク2: ワークフローが起動しない
- **原因**: ラベルの不一致、Runnerがオフライン
- **対策**:
  - ワークフローのruns-onラベルとRunnerラベルを一致させる
  - `gh api`でRunnerのオンライン状態を確認
  - ワークフローのpathsフィルターを確認

#### リスク3: テスト環境の汚染
- **原因**: クリーンアップ失敗、並行テストの干渉
- **対策**:
  - ephemeralフラグを使用して自動クリーンアップ
  - ユニークな名前（タイムスタンプ付き）を使用
  - テスト前に既存Runnerの確認と削除

#### リスク4: ネットワークタイムアウト
- **原因**: GitHub APIレート制限、ネットワーク不安定
- **対策**:
  - APIレート制限の確認: `gh api rate_limit`
  - タイムアウト値を調整（デフォルト300秒）
  - リトライロジックの実装

#### リスク5: リソース不足
- **原因**: ディスク容量不足、メモリ不足
- **対策**:
  - テスト前にディスク容量確認: `df -h`
  - _workディレクトリの定期的なクリーンアップ
  - 同時実行ジョブ数の制限

### 成功基準

1. **必須（P1）テストケース**: 100%成功
2. **推奨（P2）テストケース**: 80%以上成功
3. **オプション（P3）テストケース**: 60%以上成功

### テスト実行時間見積もり

- 環境準備: 5分
- P1テスト実行: 10分
- P2テスト実行: 15分
- P3テスト実行: 10分
- クリーンアップ: 5分
- **合計: 約45分**

### テスト結果記録

テスト結果は以下の形式で記録する：

```markdown
## テスト実行結果 - YYYY-MM-DD

### 環境情報
- Runner名: test-runner-XXXXXXXX
- GitHubリポジトリ: owner/repo
- 実行者: username
- 開始時刻: HH:MM:SS
- 終了時刻: HH:MM:SS

### テスト結果サマリ
- P1: X/4 成功
- P2: X/4 成功  
- P3: X/5 成功

### 詳細結果
| テストID | 結果 | 実行時間 | 備考 |
|---------|------|---------|------|
| T01 | ✅/❌ | XXs | - |
```

### 次のステップ

1. このテスト計画書に基づいてテストを実行
2. 結果を記録し、問題があれば課題として記録
3. 継続的インテグレーションへの組み込みを検討
4. 本番環境向けの設定ガイドを作成