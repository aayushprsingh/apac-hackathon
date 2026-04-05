"""
Gmail API Tools for Cortex
Provides email search, reading, and drafting via Gmail API
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import re

# Lazy-load the Gmail API service (requires OAuth setup)
_gmail_service = None


def get_gmail_service():
    """Get or create the Gmail API service (lazy initialization)."""
    global _gmail_service
    if _gmail_service is not None:
        return _gmail_service
    
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    
    # Check for OAuth token file
    token_file = "token.json"
    creds = None
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/gmail.modify'])
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "Gmail API not authenticated. To fix:\n"
                "1. Go to https://console.cloud.google.com/apis/credentials\n"
                "2. Create OAuth 2.0 Client ID (Desktop app)\n"
                "3. Download and save as credentials.json\n"
                "4. Run: python tools/authenticate.py --gmail\n"
            )
    
    _gmail_service = build('gmail', 'v1', credentials=creds)
    return _gmail_service


def _extract_body(payload: dict) -> str:
    """Extract plain text body from email payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' and 'body' in part:
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            elif part['mimeType'] == 'text/html' and 'body' in part:
                # Fallback to HTML if no plain text
                data = part['body'].get('data', '')
                if data:
                    # Strip HTML tags for plain text version
                    html = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    return re.sub(r'<[^>]+>', '', html)
    elif 'body' in payload:
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    return "[No body content]"


def _format_email_summary(message: dict) -> dict:
    """Format a Gmail message into a readable summary dict."""
    headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
    return {
        'id': message['id'],
        'thread_id': message['threadId'],
        'from': headers.get('From', 'Unknown'),
        'to': headers.get('To', 'Unknown'),
        'subject': headers.get('Subject', '(No subject)'),
        'date': headers.get('Date', 'Unknown'),
        'snippet': message.get('snippet', ''),
    }


def search_emails(query: str, max_results: int = 5) -> list:
    """
    Search Gmail with a query string.
    
    Common queries:
    - "from:rahul@gmail.com" — emails from specific sender
    - "subject:meeting" — emails with 'meeting' in subject
    - "is:unread" — unread emails
    - "after:2026/01/01" — emails after date
    - "label:important" — starred/important
    
    Args:
        query: Gmail search syntax string
        max_results: Number of results to return (max 50)
    
    Returns:
        list of email summaries (id, from, subject, date, snippet)
    """
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=min(max_results, 50)
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            return []
        
        email_list = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            email_list.append(_format_email_summary(message))
        
        return email_list
    except RuntimeError as e:
        return [{"error": str(e)}]
    except Exception as e:
        return [{"error": f"Failed to search emails: {str(e)}"}]


def read_email(thread_id: str = None, message_id: str = None) -> dict:
    """
    Read a full email by thread ID or message ID.
    
    Provide thread_id to get the latest message in the thread,
    or message_id to get a specific message.
    
    Args:
        thread_id: Gmail thread ID
        message_id: Specific message ID (takes precedence)
    
    Returns:
        dict with full email details including body
    """
    try:
        service = get_gmail_service()
        
        if message_id:
            msg = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
        elif thread_id:
            # Get latest message in thread
            thread = service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()
            messages = thread.get('messages', [])
            msg = messages[-1] if messages else None
            if not msg:
                return {"error": "Thread is empty"}
        else:
            return {"error": "Provide either thread_id or message_id"}
        
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        return {
            'id': msg['id'],
            'thread_id': msg['threadId'],
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', 'Unknown'),
            'cc': headers.get('Cc', ''),
            'subject': headers.get('Subject', '(No subject)'),
            'date': headers.get('Date', 'Unknown'),
            'snippet': msg.get('snippet', ''),
            'body': _extract_body(msg['payload']),
            'label_ids': msg.get('labelIds', []),
        }
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to read email: {str(e)}"}]


def get_thread(thread_id: str, max_messages: int = 10) -> dict:
    """
    Get all messages in a thread/conversation.
    
    Args:
        thread_id: Gmail thread ID
        max_messages: Maximum messages to return
    
    Returns:
        dict with thread info and list of messages
    """
    try:
        service = get_gmail_service()
        thread = service.users().threads().get(
            userId='me',
            id=thread_id
        ).execute()
        
        messages = thread.get('messages', [])[:max_messages]
        formatted_messages = []
        
        for msg in messages:
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            formatted_messages.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'to': headers.get('To', 'Unknown'),
                'subject': headers.get('Subject', '(No subject)'),
                'date': headers.get('Date', 'Unknown'),
                'body': _extract_body(msg['payload']),
            })
        
        return {
            'thread_id': thread_id,
            'total_messages': len(thread.get('messages', [])),
            'messages': formatted_messages,
        }
    except Exception as e:
        return {"error": f"Failed to get thread: {str(e)}"}


def draft_email(to: str, subject: str, body: str, cc: str = None) -> dict:
    """
    Create a Gmail draft (does NOT send).
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body
        cc: Optional CC addresses (comma-separated)
    
    Returns:
        dict with draft ID and message details
    """
    try:
        service = get_gmail_service()
        
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        
        message.attach(MIMEText(body, 'plain'))
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()
        
        return {
            'draft_id': draft['id'],
            'to': to,
            'subject': subject,
            'status': 'Draft created (not sent — awaiting user approval)',
            'preview': f"To: {to}\nSubject: {subject}\n\n{body[:200]}...",
        }
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to create draft: {str(e)}"}


def send_email(to: str, subject: str, body: str, cc: str = None) -> dict:
    """
    Send an email immediately.
    
    WARNING: This sends the email. For multi-step workflows, prefer draft_email first.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body
        cc: Optional CC
    
    Returns:
        dict with send result
    """
    try:
        service = get_gmail_service()
        
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        
        message.attach(MIMEText(body, 'plain'))
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        sent = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        
        return {
            'message_id': sent['id'],
            'thread_id': sent['threadId'],
            'to': to,
            'subject': subject,
            'status': 'Sent successfully',
        }
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


def list_recent_emails(max_results: int = 10) -> list:
    """List recent emails in inbox."""
    return search_emails("in:inbox", max_results)


def mark_as_read(message_id: str) -> dict:
    """Mark an email as read (remove UNREAD label)."""
    try:
        service = get_gmail_service()
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return {'message_id': message_id, 'status': 'Marked as read'}
    except Exception as e:
        return {'error': str(e)}
