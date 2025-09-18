# メール機能仕様書

## 概要
CLIベースのメールクライアント機能を実装する。
n8nのアーキテクチャを参考に、モジュラーな設計とする。

## 機能要件

### 1. 認証機能
- IMAP/SMTP認証をサポート
- OAuth2認証のサポート（Gmail等）
- 認証情報の安全な保存（暗号化）

### 2. メール取得機能
- IMAPプロトコルによるメール取得
- フィルタリング（未読、日付範囲、送信者等）
- ページネーション対応

### 3. 返信下書き保存機能
- 下書きの作成・編集・削除
- 自動保存機能
- テンプレート機能

### 4. データ永続化
- SQLiteによるローカル保存
- メールのキャッシュ機能
- 下書きの永続化

## データモデル

### accounts テーブル
```sql
CREATE TABLE accounts (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  provider TEXT NOT NULL, -- 'gmail', 'outlook', 'custom'
  auth_type TEXT NOT NULL, -- 'oauth2', 'password'
  encrypted_credentials TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### emails テーブル
```sql
CREATE TABLE emails (
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL,
  message_id TEXT NOT NULL UNIQUE,
  subject TEXT,
  from_address TEXT NOT NULL,
  to_addresses TEXT, -- JSON array
  cc_addresses TEXT, -- JSON array
  body_text TEXT,
  body_html TEXT,
  headers TEXT, -- JSON
  is_read BOOLEAN DEFAULT FALSE,
  received_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES accounts(id)
);
```

### drafts テーブル
```sql
CREATE TABLE drafts (
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL,
  reply_to_email_id INTEGER,
  subject TEXT,
  to_addresses TEXT, -- JSON array
  cc_addresses TEXT, -- JSON array
  body TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (reply_to_email_id) REFERENCES emails(id)
);
```

## インターフェース仕様

### CLI コマンド
```bash
# アカウント設定
mail auth add --provider gmail --email user@gmail.com
mail auth list
mail auth remove --email user@gmail.com

# メール取得
mail fetch --account user@gmail.com --unread
mail fetch --account user@gmail.com --since "2024-01-01"
mail list --account user@gmail.com --limit 10

# 下書き操作
mail draft create --to recipient@example.com --subject "Test"
mail draft edit --id 1 --body "New content"
mail draft list
mail draft delete --id 1
```

## テストシナリオ

### 認証テスト
1. 新規アカウント追加（成功/失敗）
2. 認証情報の暗号化確認
3. 無効な認証情報でのエラーハンドリング

### メール取得テスト
1. メール一覧取得
2. フィルタリング動作確認
3. ネットワークエラー時の挙動

### 下書きテスト
1. 下書き作成・編集・削除
2. 自動保存機能
3. データベース永続化確認