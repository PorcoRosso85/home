# クリーンアップタスク

## 背景

アーキテクチャの最適化に伴い、不要になったファイルの削除など、後続のクリーンアップタスクが必要になっています。このドキュメントでは、実施すべきクリーンアップタスクを定義し、優先順位付けを行います。

## 実施すべきタスク

### 1. 不要ファイルの削除 [優先度: 高]

以下のファイルは新しい構造では不要となったため、削除する必要があります：

```bash
rm /home/nixos/scheme/src/usecase/requirements-deps.ts
rm /home/nixos/scheme/src/usecase/requirements-to-function.ts
```

**注意**: これらのファイルを削除する前に、対応する新ファイルが正しく機能していることを確認してください。

### 2. 空ディレクトリの削除 [優先度: 中]

ファイル削除後、以下のディレクトリが空になった場合は削除します：

```bash
# ディレクトリが空かどうか確認
ls -la /home/nixos/scheme/src/usecase/

# 空の場合は削除
rmdir /home/nixos/scheme/src/usecase/
```

### 3. インポート参照の確認 [優先度: 高]

プロジェクト全体で、古いファイルパスを参照しているインポート文がないか確認します：

```bash
# 古いパスへの参照を検索
grep -r "usecase/requirements-deps" /home/nixos/scheme/
grep -r "usecase/requirements-to-function" /home/nixos/scheme/
```

見つかった参照は、新しいパスに更新する必要があります：

- 旧: `../usecase/requirements-deps`
- 新: `../application/requirementsDepsUsecase`

- 旧: `../usecase/requirements-to-function`
- 新: `../application/requirementsToFunctionUsecase`

### 4. Git管理からのファイル除外 [優先度: 中]

削除したファイルがGitで追跡されている場合は、Git管理から除外します：

```bash
git rm /home/nixos/scheme/src/usecase/requirements-deps.ts
git rm /home/nixos/scheme/src/usecase/requirements-to-function.ts
```

### 5. ファイル実行権限の確認 [優先度: 中]

ファイル実行権限の規約に基づいて、正しく設定されているか確認します：

```bash
# インターフェース層のファイル実行権限を確認
ls -la /home/nixos/scheme/src/interface/

# アプリケーション層のファイル実行権限を確認
ls -la /home/nixos/scheme/src/application/
```

以下の原則に従って修正します：
- インターフェース層のユーザー操作用ファイルには実行権限を付与
- アプリケーション層のファイルには実行権限は不要

## 実施計画

1. テスト環境での動作確認
2. 不要ファイルの削除
3. インポート参照の修正
4. ファイル実行権限の調整
5. 最終動作確認

## 担当者とスケジュール

- 担当者: [担当者名]
- 実施予定日: 2025年3月28日
- 完了確認: 2025年3月29日

## リスク対策

1. **バックアップの作成**
   ```bash
   # 変更前にバックアップを作成
   cp -r /home/nixos/scheme/src /home/nixos/scheme/src_backup_240328
   ```

2. **段階的実施**
   - 各ステップごとに動作確認を行い、問題があれば直ちに修正

3. **ロールバック手順**
   ```bash
   # 問題発生時のロールバック
   rm -rf /home/nixos/scheme/src
   cp -r /home/nixos/scheme/src_backup_240328 /home/nixos/scheme/src
   ```

## 完了基準

1. すべての不要ファイルが削除されている
2. すべてのインポート参照が更新されている
3. ファイル実行権限が規約に従って設定されている
4. すべてのテストが正常に完了する
