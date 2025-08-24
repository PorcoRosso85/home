# calc_partners の公開手順

プライベートモノレポから特定のflakeを自動的に公開リポジトリへ同期する設定です。

## 概要

- **プライベートリポジトリ**: `github:PorcoRosso85/home` (モノレポ)
- **公開リポジトリ**: `github:PorcoRosso85/public-flakes` (選択的公開)
- **自動同期**: GitHub Actionsでpush時に自動反映

## 初回設定（1回のみ）

### 1. 公開リポジトリの作成

```bash
# public-flakes という公開リポジトリを作成
gh repo create public-flakes --public --description "Public flakes from monorepo"
```

### 2. Personal Access Token の作成

```bash
# GitHub CLIでトークンを確認（または GitHub Settings > Developer settings から作成）
gh auth token

# 必要な権限:
# - repo (Full control of private repositories)
# - workflow (Update GitHub Action workflows)
```

### 3. プライベートリポジトリに Secret を登録

```bash
# PUBLIC_REPO_TOKEN という名前で登録
gh secret set PUBLIC_REPO_TOKEN -R PorcoRosso85/home
# プロンプトが出たらトークンを貼り付け
```

### 4. GitHub Actions ワークフローの設定

プライベートリポジトリ（home）に以下のファイルを作成：

`.github/workflows/sync-calc-partners.yml`:

```yaml
name: Sync calc_partners to Public
on:
  push:
    branches: [main, dev]
    paths:
      - 'bin/src/poc/calc_partners/**'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout private repo
        uses: actions/checkout@v3
      
      - name: Sync to public repo
        env:
          PUBLIC_REPO_TOKEN: ${{ secrets.PUBLIC_REPO_TOKEN }}
        run: |
          # 公開リポジトリをクローン
          git clone https://${PUBLIC_REPO_TOKEN}@github.com/PorcoRosso85/public-flakes.git
          
          # calc_partners を同期（既存を削除して新規コピー）
          rm -rf public-flakes/calc_partners
          cp -r bin/src/poc/calc_partners public-flakes/
          
          # 公開リポジトリへプッシュ
          cd public-flakes
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          
          # 変更がある場合のみコミット
          if git diff --staged --quiet; then
            echo "No changes to sync"
          else
            git commit -m "sync: update calc_partners from private repo

            Source: ${{ github.sha }}
            Triggered by: ${{ github.event.head_commit.message }}"
            git push origin main
          fi
```

## 運用方法

### 通常の開発フロー

```bash
# プライベートリポジトリで普通に開発
cd ~/bin/src/poc/calc_partners

# 編集作業...
vim some_file.nix

# コミット & プッシュ
git add .
git commit -m "feat: add new feature"
git push

# → 自動的に public-flakes リポジトリへ反映される！
```

### 公開リポジトリの利用方法

利用者は以下のように使用可能：

```bash
# 直接実行
nix run github:PorcoRosso85/public-flakes#calc_partners

# または flake.nix で参照
{
  inputs = {
    calc-partners.url = "github:PorcoRosso85/public-flakes?dir=calc_partners";
  };
}
```

## 複数のflakeを公開する場合

ワークフローのpathsとスクリプトを拡張：

```yaml
paths:
  - 'bin/src/poc/calc_partners/**'
  - 'bin/src/poc/another_app/**'  # 追加

# スクリプト部分も対応するディレクトリをコピー
cp -r bin/src/poc/another_app public-flakes/
```

## トラブルシューティング

### 同期が動作しない場合

1. **Actions タブを確認**: リポジトリの Actions タブでワークフローの実行状況を確認
2. **Secret の確認**: `gh secret list -R PorcoRosso85/home` で PUBLIC_REPO_TOKEN が存在するか確認
3. **トークンの権限**: repo権限があることを確認
4. **ブランチ名**: ワークフローのbranchesがpush先と一致しているか確認

### 手動で同期したい場合

```bash
# GitHub Actions を手動実行
gh workflow run sync-calc-partners.yml -R PorcoRosso85/home
```

## メリット

- ✅ pushするだけで自動同期
- ✅ ローカルでの追加操作不要
- ✅ 選択的に公開するflakeを制御可能
- ✅ プライベートリポジトリの構造を維持
- ✅ 公開リポジトリは常に最新

## 注意事項

- プライベートな情報（APIキー、内部ドキュメント等）が含まれていないか確認
- `.gitignore` や `.env` ファイルは同期されないよう注意
- 公開リポジトリ側での直接編集は避ける（次回同期で上書きされる）