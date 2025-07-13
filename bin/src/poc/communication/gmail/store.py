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


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def setup():
    """Gmail API設定ガイドを表示"""
    print("""
Gmail API Setup Required:

1. Google Cloud Console (https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成または既存プロジェクトを選択
3. Gmail API を有効化
4. 認証情報 > OAuth 2.0 クライアント ID を作成
   - アプリケーションタイプ: デスクトップアプリケーション
5. JSON形式の認証情報をダウンロード
6. 以下の環境変数を設定:

export GMAIL_CLIENT_ID="your_client_id"
export GMAIL_CLIENT_SECRET="your_client_secret"

7. 再実行してください
    """)


def get_gmail_service():
    """Gmail API サービスを取得"""
    client_id = os.getenv('GMAIL_CLIENT_ID')
    client_secret = os.getenv('GMAIL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: Gmail credentials not found in environment variables")
        setup()
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
            # Create credentials dict for OAuth flow (Desktop application type)
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            
            try:
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                # Desktop application用: 手動認証フローを使用
                print("\nManual authentication required:")
                print("1. Open this URL in your browser:")
                flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                auth_url, _ = flow.authorization_url(
                    prompt='consent',
                    access_type='offline'
                )
                print(f"   {auth_url}")
                print("2. After authorization, copy the authorization code and paste it here:")
                auth_code = input("Authorization code: ").strip()
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
            except Exception as e:
                print(f"Authentication failed: {e}")
                print("\nPlease check your credentials and try again.")
                setup()
                sys.exit(1)
        
        # Save credentials for future use
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Failed to build Gmail service: {e}")
        setup()
        sys.exit(1)


def fetch_emails(max_results=10):
    """Gmailからメールを取得してデータベースに保存"""
    try:
        service = get_gmail_service()
        db = EmailDB()
        
        # メールリストを取得
        results = service.users().messages().list(
            userId='me', 
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        print(f"Found {len(messages)} messages")
        
        for message in messages:
            msg_id = message['id']
            
            # 既に保存済みかチェック
            if db.email_exists(f"gmail_{msg_id}"):
                print(f"Skipping already stored message: {msg_id}")
                continue
            
            # メール詳細を取得
            msg = service.users().messages().get(
                userId='me', 
                id=msg_id
            ).execute()
            
            # メタデータを抽出
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            recipient = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
            
            # 本文を抽出
            body = extract_body(msg['payload'])
            
            # タイムスタンプを変換
            timestamp = datetime.fromtimestamp(int(msg['internalDate']) / 1000)
            
            # データベースに保存
            db.store_email(
                email_id=f"gmail_{msg_id}",
                provider="gmail",
                subject=subject,
                sender=sender,
                recipient=recipient,
                body=body,
                timestamp=timestamp,
                raw_data=msg
            )
            
            print(f"Stored: {subject[:50]}...")
    
    except HttpError as error:
        print(f"Gmail API error: {error}")
        if error.resp.status == 401:
            print("Authentication failed. Removing token and retrying...")
            token_path = Path('token.json')
            if token_path.exists():
                token_path.unlink()
            setup()
        sys.exit(1)
    except Exception as error:
        print(f"Unexpected error: {error}")
        sys.exit(1)


def extract_body(payload):
    """メール本文を抽出"""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
            elif part['mimeType'] == 'text/html':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
    else:
        if payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
    
    return body


if __name__ == "__main__":
    fetch_emails()