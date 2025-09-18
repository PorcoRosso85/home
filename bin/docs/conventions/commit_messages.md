# コミットメッセージ規約

## 基本方針

プロジェクトのコミット履歴は、変更内容を追跡するための重要なドキュメントです。
我々は [Conventional Commits](https://www.conventionalcommits.org/) の仕様に準拠します。
これにより、変更履歴の可読性を高め、CHANGELOGの自動生成やセマンティックバージョニングを容易にします。

## フォーマット

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Type (必須)

- `feat`: 新機能の追加
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの動作に影響しない、フォーマットなどの変更
- `refactor`: リファクタリング（バグ修正や機能追加を含まない）
- `perf`: パフォーマンス改善
- `test`: テストの追加・修正
- `build`: ビルドシステムや外部依存に関する変更
- `ci`: CI設定やスクリプトの変更
- `chore`: 上記のいずれにも当てはまらない雑多な変更

### Scope (任意)

変更が影響する範囲を示します。（例: `auth`, `api`, `db`）

### Description (必須)

変更内容を簡潔に説明する一文。現在形で記述し、大文字で始めない。

### Body (任意)

変更の動機や、より詳細な説明を記述します。

### Footer (任意)

`BREAKING CHANGE:` や、関連するIssue番号 (`Closes #123`) などを記述します。

## 使用例

```
feat(auth): ユーザー登録APIを追加

メールアドレスとパスワードによるユーザー登録機能を実装。
パスワードはbcryptでハッシュ化して保存する。

Closes #42
```

```
fix: プロフィール画像が円形に表示されないバグを修正

CSSの`border-radius`の指定が間違っていたため修正しました。
```
