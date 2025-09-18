"""
メールCLI機能の失敗するテストケース（TDD Red Phase）
"""
import pytest
import sqlite3
from pathlib import Path
from typing import List, Dict, Any


class TestMailAuthentication:
    """認証機能のテスト"""
    
    def test_add_gmail_account_with_oauth2(self):
        """GmailアカウントをOAuth2で追加できる"""
        # Arrange
        email = "test@gmail.com"
        
        # Act
        result = add_mail_account(provider="gmail", email=email, auth_type="oauth2")
        
        # Assert
        assert result.success is True
        assert result.account.email == email
        assert result.account.provider == "gmail"
    
    def test_invalid_credentials_shows_clear_error(self):
        """無効な認証情報で明確なエラーメッセージが表示される"""
        # Arrange
        email = "invalid@gmail.com"
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            add_mail_account(provider="gmail", email=email, auth_type="password", password="wrong")
        
        assert "認証に失敗しました" in str(exc_info.value)
        assert "パスワードを確認してください" in str(exc_info.value)
    
    def test_credentials_are_encrypted_in_database(self):
        """認証情報がデータベースに暗号化されて保存される"""
        # Arrange
        email = "secure@gmail.com"
        password = "secret123"
        
        # Act
        add_mail_account(provider="gmail", email=email, auth_type="password", password=password)
        
        # Assert
        db = get_database_connection()
        cursor = db.execute("SELECT encrypted_credentials FROM accounts WHERE email = ?", (email,))
        encrypted = cursor.fetchone()[0]
        
        assert encrypted != password
        assert len(encrypted) > 50  # 暗号化されたデータは長い
        assert decrypt_credentials(encrypted)["password"] == password


class TestMailFetching:
    """メール取得機能のテスト"""
    
    def test_fetch_unread_emails(self):
        """未読メールのみを取得できる"""
        # Arrange
        account = create_test_account()
        
        # Act
        emails = fetch_emails(account=account.email, unread_only=True)
        
        # Assert
        assert len(emails) > 0
        assert all(not email.is_read for email in emails)
    
    def test_fetch_emails_with_date_filter(self):
        """日付でフィルタリングしてメールを取得できる"""
        # Arrange
        account = create_test_account()
        since_date = "2024-01-01"
        
        # Act
        emails = fetch_emails(account=account.email, since=since_date)
        
        # Assert
        assert all(email.received_at >= since_date for email in emails)
    
    def test_emails_are_cached_locally(self):
        """取得したメールがローカルDBにキャッシュされる"""
        # Arrange
        account = create_test_account()
        
        # Act
        emails = fetch_emails(account=account.email, limit=10)
        
        # Assert
        db = get_database_connection()
        cursor = db.execute("SELECT COUNT(*) FROM emails WHERE account_id = ?", (account.id,))
        cached_count = cursor.fetchone()[0]
        
        assert cached_count >= len(emails)
    
    def test_network_error_returns_cached_emails(self):
        """ネットワークエラー時はキャッシュされたメールを返す"""
        # Arrange
        account = create_test_account()
        fetch_emails(account=account.email, limit=5)  # 事前にキャッシュ
        simulate_network_error()
        
        # Act
        emails = fetch_emails(account=account.email, limit=5)
        
        # Assert
        assert len(emails) == 5
        assert all(email.from_cache for email in emails)


class TestDraftManagement:
    """下書き管理機能のテスト"""
    
    def test_create_draft_with_basic_fields(self):
        """基本的なフィールドで下書きを作成できる"""
        # Arrange
        account = create_test_account()
        
        # Act
        draft = create_draft(
            account=account.email,
            to=["recipient@example.com"],
            subject="Test Draft",
            body="This is a test"
        )
        
        # Assert
        assert draft.id is not None
        assert draft.subject == "Test Draft"
        assert draft.to_addresses == ["recipient@example.com"]
    
    def test_draft_auto_save_every_30_seconds(self):
        """下書きが30秒ごとに自動保存される"""
        # Arrange
        account = create_test_account()
        draft = create_draft(account=account.email, to=["test@example.com"])
        
        # Act
        draft.body = "Updated content"
        wait_seconds(31)
        
        # Assert
        saved_draft = get_draft(draft.id)
        assert saved_draft.body == "Updated content"
        assert saved_draft.updated_at > draft.created_at
    
    def test_reply_draft_links_to_original_email(self):
        """返信の下書きが元のメールにリンクされる"""
        # Arrange
        account = create_test_account()
        original_email = fetch_emails(account=account.email, limit=1)[0]
        
        # Act
        reply_draft = create_reply_draft(
            account=account.email,
            reply_to=original_email.id,
            body="This is my reply"
        )
        
        # Assert
        assert reply_draft.reply_to_email_id == original_email.id
        assert original_email.from_address in reply_draft.to_addresses
        assert reply_draft.subject.startswith("Re: ")


class TestCLIInterface:
    """CLIインターフェースのテスト"""
    
    def test_mail_auth_add_command(self, cli_runner):
        """mail auth addコマンドが動作する"""
        # Act
        result = cli_runner.invoke(["mail", "auth", "add", "--provider", "gmail", "--email", "test@gmail.com"])
        
        # Assert
        assert result.exit_code == 0
        assert "認証に成功しました" in result.output
    
    def test_mail_fetch_command_with_filters(self, cli_runner):
        """mail fetchコマンドでフィルタが動作する"""
        # Arrange
        create_test_account_with_cli(cli_runner)
        
        # Act
        result = cli_runner.invoke(["mail", "fetch", "--account", "test@gmail.com", "--unread"])
        
        # Assert
        assert result.exit_code == 0
        assert "未読メール" in result.output
    
    def test_mail_draft_create_interactive(self, cli_runner):
        """mail draft createコマンドで対話的に下書きを作成できる"""
        # Arrange
        create_test_account_with_cli(cli_runner)
        
        # Act
        result = cli_runner.invoke(
            ["mail", "draft", "create"],
            input="test@example.com\nTest Subject\nTest Body\n"
        )
        
        # Assert
        assert result.exit_code == 0
        assert "下書きを保存しました" in result.output


class TestOfflineCapability:
    """オフライン機能のテスト"""
    
    def test_draft_operations_work_offline(self):
        """オフライン時でも下書き操作が可能"""
        # Arrange
        account = create_test_account()
        simulate_offline_mode()
        
        # Act
        draft = create_draft(account=account.email, to=["offline@test.com"])
        draft.body = "Edited offline"
        save_draft(draft)
        
        # Assert
        saved_draft = get_draft(draft.id)
        assert saved_draft.body == "Edited offline"
    
    def test_queued_operations_sync_when_online(self):
        """オンライン復帰時にキューイングされた操作が同期される"""
        # Arrange
        account = create_test_account()
        simulate_offline_mode()
        
        # Act
        mark_email_as_read(email_id=1)
        delete_email(email_id=2)
        simulate_online_mode()
        wait_for_sync()
        
        # Assert
        sync_status = get_sync_status()
        assert sync_status.pending_operations == 0
        assert sync_status.last_sync_success is True


# ヘルパー関数（実装されていないため、テストは失敗する）
def add_mail_account(provider: str, email: str, auth_type: str, password: str = None):
    raise NotImplementedError("add_mail_account not implemented")

def fetch_emails(account: str, unread_only: bool = False, since: str = None, limit: int = None):
    raise NotImplementedError("fetch_emails not implemented")

def create_draft(account: str, to: List[str], subject: str = "", body: str = ""):
    raise NotImplementedError("create_draft not implemented")

def create_reply_draft(account: str, reply_to: int, body: str):
    raise NotImplementedError("create_reply_draft not implemented")

def get_database_connection():
    raise NotImplementedError("get_database_connection not implemented")

def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
    raise NotImplementedError("decrypt_credentials not implemented")

def create_test_account():
    raise NotImplementedError("create_test_account not implemented")

def simulate_network_error():
    raise NotImplementedError("simulate_network_error not implemented")

def wait_seconds(seconds: int):
    raise NotImplementedError("wait_seconds not implemented")

def get_draft(draft_id: int):
    raise NotImplementedError("get_draft not implemented")

def save_draft(draft):
    raise NotImplementedError("save_draft not implemented")

def simulate_offline_mode():
    raise NotImplementedError("simulate_offline_mode not implemented")

def simulate_online_mode():
    raise NotImplementedError("simulate_online_mode not implemented")

def mark_email_as_read(email_id: int):
    raise NotImplementedError("mark_email_as_read not implemented")

def delete_email(email_id: int):
    raise NotImplementedError("delete_email not implemented")

def wait_for_sync():
    raise NotImplementedError("wait_for_sync not implemented")

def get_sync_status():
    raise NotImplementedError("get_sync_status not implemented")

def create_test_account_with_cli(cli_runner):
    raise NotImplementedError("create_test_account_with_cli not implemented")


class AuthenticationError(Exception):
    pass