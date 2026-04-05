"""
Firebase Auth Backend for Cortex
Uses Firebase Admin SDK for server-side token verification
AND Gmail/Calendar API for automatic data pulling on sign-in.
"""

import os
import json
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from functools import wraps

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Google APIs for Gmail/Calendar auto-pull
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# =============================================================================
# FIREBASE ADMIN INITIALIZATION
# =============================================================================

firebase_initialized = False

def init_firebase():
    """Initialize Firebase Admin SDK using service account."""
    global firebase_initialized
    if firebase_initialized:
        return True

    # Try to load from GOOGLE_APPLICATION_CREDENTIALS env var
    # This is a path to the service account JSON file
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path or not os.path.exists(creds_path):
        # Try default path
        creds_path = '/app/firebase-credentials.json'

    if os.path.exists(creds_path):
        try:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print(f"[Firebase] Initialized with service account: {creds_path}")
            return True
        except Exception as e:
            print(f"[Firebase] Init failed: {e}")

    print("[Firebase] Not initialized — set GOOGLE_APPLICATION_CREDENTIALS env var")
    return False


def get_firestore():
    """Get Firestore client if Firebase is initialized."""
    if firebase_initialized:
        try:
            return firestore.client()
        except:
            pass
    return None


# =============================================================================
# USER DATA IN FIRESTORE
# =============================================================================

def get_user_firestore_data(uid):
    """Get all user data from Firestore."""
    db = get_firestore()
    if not db:
        return None

    try:
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            return user_doc.to_dict()
    except Exception as e:
        print(f"[Firestore] Error getting user data: {e}")

    return None


def save_user_firestore_data(uid, data):
    """Save user data to Firestore."""
    db = get_firestore()
    if not db:
        return False

    try:
        db.collection('users').document(uid).set(data, merge=True)
        return True
    except Exception as e:
        print(f"[Firestore] Error saving user data: {e}")
        return False


def get_user_memory(uid):
    """Get user's memory entries from Firestore."""
    db = get_firestore()
    if not db:
        return []

    try:
        docs = db.collection('users').document(uid).collection('memory').get()
        return [{'id': doc.id, **doc.to_dict()} for doc in docs]
    except:
        return []


def save_user_memory(uid, key, value, confidence=0.9, source='chat'):
    """Save a memory entry to Firestore."""
    db = get_firestore()
    if not db:
        return None

    try:
        doc_ref = db.collection('users').document(uid).collection('memory').document(key)
        doc_ref.set({
            'key': key,
            'value': value,
            'confidence': confidence,
            'source': source,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return {'key': key, 'value': value}
    except Exception as e:
        print(f"[Firestore] Error saving memory: {e}")
        return None


# =============================================================================
# GMAIL API — AUTOMATIC EMAIL PULL
# =============================================================================

def build_gmail_service(credentials_dict):
    """Build Gmail service from OAuth credentials."""
    creds = Credentials.from_authorized_user_info(
        credentials_dict,
        scopes=['https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.compose']
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build('gmail', 'v1', credentials=creds)


def pull_gmail_data(service, max_results=10):
    """Pull relevant emails for briefing."""
    try:
        # Get recent inbox emails
        results = service.users().messages().list(
            userId='me',
            q='is:inbox newer_than:7d',
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return []

        emails = []
        for msg in messages[:5]:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}

            # Extract body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'body' in part:
                        data = part['body'].get('data', '')
                        if data:
                            import base64
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')[:500]
                            break

            emails.append({
                'id': message['id'],
                'from': headers.get('From', ''),
                'subject': headers.get('Subject', '(No subject)'),
                'date': headers.get('Date', ''),
                'snippet': message.get('snippet', ''),
                'body_preview': body[:300] if body else ''
            })

        return emails
    except Exception as e:
        print(f"[Gmail] Error pulling emails: {e}")
        return []


def pull_gmail_tasks(service):
    """Scan emails for task-like content (deadlines, follow-ups, etc.)."""
    try:
        # Search for emails that might contain tasks
        results = service.users().messages().list(
            userId='me',
            q='subject:(todo OR task OR deadline OR follow-up OR "need to" OR "should" OR "must") newer_than:14d',
            maxResults=10
        ).execute()

        messages = results.get('messages', [])
        tasks_found = []

        for msg in messages[:5]:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
            snippet = message.get('snippet', '')

            tasks_found.append({
                'source': 'gmail',
                'from': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'snippet': snippet[:200]
            })

        return tasks_found
    except Exception as e:
        print(f"[Gmail] Error scanning for tasks: {e}")
        return []


# =============================================================================
# GOOGLE CALENDAR API — AUTOMATIC CALENDAR PULL
# =============================================================================

def build_calendar_service(credentials_dict):
    """Build Calendar service from OAuth credentials."""
    creds = Credentials.from_authorized_user_info(
        credentials_dict,
        scopes=['https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/calendar.events']
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build('calendar', 'v3', credentials=creds)


def pull_calendar_data(service, days=7):
    """Pull calendar events for the next N days."""
    try:
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'

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

            formatted.append({
                'id': event['id'],
                'summary': event.get('summary', '(No title)'),
                'start': start.get('dateTime', start.get('date', '')),
                'end': end.get('dateTime', end.get('date', '')),
                'is_all_day': 'date' in start and 'dateTime' not in start,
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'attendees': [
                    a.get('email', '') for a in event.get('attendees', []) if a.get('email')
                ],
                'status': event.get('status', ''),
            })

        return formatted
    except Exception as e:
        print(f"[Calendar] Error pulling events: {e}")
        return []


# =============================================================================
# COMPLETE USER ONBOARDING — PULLS ALL DATA AUTOMATICALLY
# =============================================================================

def onboard_user_with_google_data(uid, google_tokens, user_email, user_name):
    """
    When a user signs in with Google, automatically pull:
    1. Their Gmail emails
    2. Their Calendar events
    3. Task-like content from emails
    4. Store everything in Firestore
    """
    gmail_service = None
    calendar_service = None

    try:
        gmail_service = build_gmail_service(google_tokens)
    except Exception as e:
        print(f"[Google] Could not initialize Gmail: {e}")

    try:
        calendar_service = build_calendar_service(google_tokens)
    except Exception as e:
        print(f"[Google] Could not initialize Calendar: {e}")

    # Pull data
    emails = pull_gmail_data(gmail_service) if gmail_service else []
    calendar_events = pull_calendar_data(calendar_service) if calendar_service else []
    tasks_from_email = pull_gmail_tasks(gmail_service) if gmail_service else []

    # Build user data
    user_data = {
        'uid': uid,
        'email': user_email,
        'name': user_name,
        'onboarding_complete': True,
        'onboarded_at': firestore.SERVER_TIMESTAMP if firebase_initialized else datetime.now().isoformat(),

        # Auto-pulled Google data
        'google_data': {
            'emails': emails,
            'calendar_events': calendar_events,
            'tasks_from_email': tasks_from_email,
            'pulled_at': datetime.now().isoformat()
        },

        # User's memory model — seeded from Google data
        'profile': {
            'name': user_name,
            'email': user_email,
            'briefing_style': 'balanced',
            'current_project': {},
        },

        'tasks': [],
        'memory': [],
    }

    # Seed memory from calendar
    for event in calendar_events[:5]:
        if event.get('summary'):
            user_data['memory'].append({
                'key': f'event_{event["id"]}',
                'value': {
                    'type': 'calendar_event',
                    'title': event['summary'],
                    'when': event.get('start', ''),
                    'attendees': event.get('attendees', [])
                },
                'confidence': 1.0,
                'source': 'calendar'
            })

    # Seed tasks from email scan
    for task in tasks_from_email[:3]:
        user_data['tasks'].append({
            'title': f'Follow up: {task["subject"][:80]}',
            'description': f'From email by {task["from"]}: {task["snippet"]}',
            'status': 'pending',
            'priority': 'medium',
            'source': 'gmail'
        })

    # Save to Firestore
    save_user_firestore_data(uid, user_data)

    print(f"[Onboarding] {user_name} ({user_email}): {len(emails)} emails, {len(calendar_events)} calendar events, {len(tasks_from_email)} tasks from email")

    return user_data


# =============================================================================
# VERIFY FIREBASE TOKEN (called from Flask route)
# =============================================================================

def verify_firebase_token(id_token):
    """Verify a Firebase ID token and return user info."""
    if not firebase_initialized:
        return None

    try:
        decoded = auth.verify_id_token(id_token)
        return {
            'uid': decoded.get('uid'),
            'email': decoded.get('email'),
            'name': decoded.get('name', decoded.get('email', '').split('@')[0]),
            'picture': decoded.get('picture', ''),
        }
    except Exception as e:
        print(f"[Firebase] Token verification failed: {e}")
        return None


def get_user_oauth_tokens(uid):
    """Get stored OAuth tokens for a user (from Firestore custom claims or doc)."""
    db = get_firestore()
    if not db:
        return None

    try:
        doc = db.collection('users').document(uid).get()
        if doc.exists:
            data = doc.to_dict()
            tokens = data.get('oauth_tokens', {})
            if tokens.get('access_token'):
                return tokens
    except:
        pass

    return None
