"""
Google OAuth integration for Cortex — Gmail + Calendar auto-pull
Without Firebase, we use direct Google OAuth 2.0 instead.

Setup:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application type)
3. Add redirect URI: https://YOUR_CLOUD_RUN_URL/api/auth/google/callback
4. Set environment variables:
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=https://YOUR_CLOUD_RUN_URL/api/auth/google/callback
"""

import os
import json
import sqlite3
from datetime import datetime

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', '')


def is_google_oauth_configured():
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)


def get_authorization_url(state_token=None):
    """Generate the Google OAuth authorization URL."""
    from google_auth_oauthlib.flow import Flow
    if not is_google_oauth_configured():
        return None
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "scope": SCOPES,
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    
    # Generate state token to prevent CSRF
    import secrets
    state = state_token or secrets.token_urlsafe(32)
    
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',  # Force consent to get refresh token
        state=state,
    )
    return authorization_url, state, flow


def exchange_code_for_tokens(code, state=None, state_token=None):
    """Exchange authorization code for access + refresh tokens."""
    from google_auth_oauthlib.flow import Flow
    
    if not is_google_oauth_configured():
        return None, "Google OAuth not configured"
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "scope": SCOPES,
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    
    try:
        flow.fetch_token(code=code, state=state_token)
        credentials = flow.credentials
        
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
        }, None
    except Exception as e:
        return None, str(e)


def save_user_google_tokens(user_id, tokens):
    """Save Google OAuth tokens to SQLite for a user."""
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(DATA_DIR, exist_ok=True)
    db_path = os.path.join(DATA_DIR, 'cortex_users.db')
    
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS google_tokens (
            user_id TEXT PRIMARY KEY,
            tokens_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.execute(
        'INSERT OR REPLACE INTO google_tokens (user_id, tokens_json, updated_at) VALUES (?, ?, ?)',
        (user_id, json.dumps(tokens), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_user_google_tokens(user_id):
    """Retrieve Google OAuth tokens for a user from SQLite."""
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
    db_path = os.path.join(DATA_DIR, 'cortex_users.db')
    
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        'SELECT tokens_json FROM google_tokens WHERE user_id = ?', (user_id,)
    ).fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None


def refresh_google_token(tokens):
    """Refresh an expired Google access token using the refresh token."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    
    creds = Credentials(
        token=tokens.get('token'),
        refresh_token=tokens.get('refresh_token'),
        token_uri=tokens.get('token_uri'),
        client_id=tokens.get('client_id'),
        client_secret=tokens.get('client_secret'),
        scopes=tokens.get('scopes', SCOPES),
    )
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        return {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expiry.isoformat() if creds.expiry else None,
        }
    return tokens


def pull_gmail_data(tokens, max_results=20):
    """Pull recent emails from Gmail using stored tokens."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import base64, re
    
    creds = Credentials(
        token=tokens.get('token'),
        refresh_token=tokens.get('refresh_token'),
        token_uri=tokens.get('token_uri'),
        client_id=tokens.get('client_id'),
        client_secret=tokens.get('client_secret'),
        scopes=['https://www.googleapis.com/auth/gmail.modify'],
    )
    
    # Refresh if needed
    if creds.expired:
        creds.refresh(Request())
    
    service = build('gmail', 'v1', credentials=creds)
    
    # Get recent emails
    results = service.users().messages().list(
        userId='me',
        q='in:inbox',
        maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    emails = []
    
    for msg in messages:
        message = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()
        
        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
        
        # Extract body
        body = ''
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'body' in part:
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')[:200]
                        break
        
        emails.append({
            'id': message['id'],
            'from': headers.get('From', 'Unknown'),
            'subject': headers.get('Subject', '(No subject)'),
            'date': headers.get('Date', ''),
            'snippet': message.get('snippet', ''),
            'body_preview': body,
            'labels': message.get('labelIds', []),
        })
    
    return emails


def pull_calendar_data(tokens, days_ahead=7):
    """Pull upcoming calendar events using stored tokens."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from datetime import datetime, timedelta
    
    creds = Credentials(
        token=tokens.get('token'),
        refresh_token=tokens.get('refresh_token'),
        token_uri=tokens.get('token_uri'),
        client_id=tokens.get('client_id'),
        client_secret=tokens.get('client_secret'),
        scopes=['https://www.googleapis.com/auth/calendar'],
    )
    
    if creds.expired:
        creds.refresh(Request())
    
    service = build('calendar', 'v3', credentials=creds)
    
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        maxResults=20,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    formatted = []
    for event in events:
        start = event.get('start', {})
        end = event.get('end', {})
        start_str = start.get('dateTime', start.get('date', 'All day'))
        end_str = end.get('dateTime', end.get('date', ''))
        
        formatted.append({
            'id': event['id'],
            'summary': event.get('summary', '(No title)'),
            'start': start_str,
            'end': end_str,
            'is_all_day': 'date' in start and 'dateTime' not in start,
            'location': event.get('location', ''),
            'attendees': [a.get('email', '') for a in event.get('attendees', []) if a.get('email')],
            'description': event.get('description', ''),
        })
    
    return formatted


def get_user_info(tokens):
    """Get user info (name, email) from Google account."""
    import requests
    
    creds = tokens
    resp = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f"Bearer {creds.get('token', '')}"}
    )
    if resp.ok:
        return resp.json()
    return {}
