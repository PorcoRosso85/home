import os
import sys
import base64
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

# Add parent directory to path for common imports
sys.path.append(str(Path(__file__).parent.parent))
from common.db import EmailDB

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose'  # 下書き作成用
]

def get_gmail_service():
    """Gmail API サービスを取得（store.pyから流用）"""
    client_id = os.getenv('GMAIL_CLIENT_ID')
    client_secret = os.getenv('GMAIL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: Gmail credentials not found in environment variables")
        print("Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET")
        sys.exit(1)
    
    creds = None
    token_path = Path('token.json')
    
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None
        
        if not creds:
            print("需要重新认证以获取撰写权限...")
            sys.exit(1)
        
        # Save updated credentials
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Failed to build Gmail service: {e}")
        sys.exit(1)

def create_draft_reply(email_id):
    """指定されたメールIDに対する返信下書きを作成"""
    try:
        service = get_gmail_service()
        db = EmailDB()
        
        # データベースからメール情報を取得
        with db.db_path.open() as conn:
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.execute("""
                SELECT subject, sender, recipient, body 
                FROM emails WHERE id = ?
            """, (email_id,))
            result = cursor.fetchone()
            
        if not result:
            print(f"メールID {email_id} が見つかりません")
            return
        
        subject, sender, recipient, body = result
        
        # 返信メッセージを作成
        reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
        reply_body = f"""
テストメッセージです。

このメールは下書き保存のテストとして自動生成されました。
元メールの件名: {subject}
元メールの送信者: {sender}

---
Original message preview:
{body[:200] if body else 'No body content'}...
        """
        
        # 送信者からメールアドレス部分を抽出
        import re
        email_match = re.search(r'<([^>]+)>', sender)
        reply_to_email = email_match.group(1) if email_match else sender
        
        # MIMEメッセージを作成
        message = MIMEText(reply_body, 'plain', 'utf-8')
        message['to'] = reply_to_email
        message['subject'] = reply_subject
        
        print(f"Reply to: {reply_to_email}")
        print(f"Subject: {reply_subject}")
        
        # メッセージをbase64エンコード
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # 下書きを作成
        draft_body = {
            'message': {
                'raw': raw_message
            }
        }
        
        draft = service.users().drafts().create(
            userId='me',
            body=draft_body
        ).execute()
        
        print(f"✅ 下書き作成成功!")
        print(f"下書きID: {draft['id']}")
        print(f"件名: {reply_subject}")
        print(f"宛先: {sender}")
        print("\nGmailの下書きフォルダで確認できます。")
        
        return draft['id']
        
    except HttpError as error:
        print(f"Gmail API error: {error}")
        if error.resp.status == 403:
            print("権限が不足しています。compose権限が必要です。")
        sys.exit(1)
    except Exception as error:
        print(f"Unexpected error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    # テスト用メールID
    test_email_id = "gmail_198020d5345a5c17"
    print(f"メール '{test_email_id}' に対する返信下書きを作成中...")
    
    draft_id = create_draft_reply(test_email_id)
    if draft_id:
        print(f"\n下書きが正常に作成されました: {draft_id}")