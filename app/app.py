"""
Cortex Flask App — Multi-User with Firebase Auth + Auto Gmail/Calendar Pull
Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

Auth: Firebase Auth (Google OAuth) when configured, demo token fallback otherwise.
Data: Firebase Firestore for persistence, Gmail + Calendar API for auto-pull.
"""

import os
import json
import uuid
import hashlib
import hmac
import time
import base64
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', os.urandom(32))
CORS(app)

DEMO_MODE = os.getenv('DEMO_MODE', '').lower() not in ('false', '0', 'no', 'off')

# =============================================================================
# FIREBASE INITIALIZATION
# =============================================================================

firebase_initialized = False
try:
    from app import firebase_auth as fb
    if hasattr(fb, '_use_firebase') and fb._use_firebase and hasattr(fb, 'init_firebase'):
        if fb.init_firebase():
            firebase_initialized = True
            print("[App] Firebase Admin initialized successfully")
        else:
            print("[App] Firebase not initialized — demo + email/password mode")
    else:
        print("[App] Firebase disabled — demo + email/password mode")
        fb = None
except ImportError:
    print("[App] firebase_auth module not found — demo + email/password mode")
    fb = None
except Exception as e:
    print(f"[App] Firebase init error: {e} — demo + email/password mode")
    fb = None

# =============================================================================
# PERSISTENT STORAGE — SQLite for user accounts + sessions ( survives restarts)
# =============================================================================
# PERSISTENT STORAGE — SQLite for user accounts + sessions ( survives restarts)
# =============================================================================
import sqlite3
import os

# Use /tmp on Cloud Run, local data/ for local development
if os.getenv('K_SERVICE'):  # Cloud Run environment
    DATA_DIR = '/tmp'
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(DATA_DIR, exist_ok=True)
USER_DB = os.path.join(DATA_DIR, 'cortex_users.db')

def _get_user_db():
    conn = sqlite3.connect(USER_DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_accounts (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            uid TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at REAL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at REAL,
            onboarding_complete INTEGER DEFAULT 1,
            source TEXT DEFAULT 'email'
        )
    ''')
    conn.commit()
    return conn


def _load_user_accounts():
    """Load user accounts from SQLite into memory."""
    global _user_accounts
    try:
        conn = _get_user_db()
        rows = conn.execute('SELECT email, password_hash, uid, name, created_at FROM user_accounts').fetchall()
        conn.close()
        for row in rows:
            _user_accounts[row[0]] = {
                'password_hash': row[1],
                'uid': row[2],
                'name': row[3],
                'created_at': row[4],
            }
    except Exception as e:
        print(f"[UserDB] Error loading accounts: {e}")


def _save_user_account(email, password_hash, uid, name, created_at):
    """Save a new user account to SQLite."""
    try:
        conn = _get_user_db()
        conn.execute(
            'INSERT OR REPLACE INTO user_accounts (email, password_hash, uid, name, created_at) VALUES (?, ?, ?, ?, ?)',
            (email, password_hash, uid, name, created_at)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[UserDB] Error saving account: {e}")


def _save_session(token, user_id, email, name, created_at, onboarding_complete, source):
    """Save a session to SQLite."""
    try:
        conn = _get_user_db()
        conn.execute(
            'INSERT OR REPLACE INTO sessions (token, user_id, email, name, created_at, onboarding_complete, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (token, user_id, email, name, created_at, 1 if onboarding_complete else 0, source)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[UserDB] Error saving session: {e}")


# In-memory user accounts storage
_user_accounts = {}

# Load existing accounts on startup (gracefully skip if DB fails)
try:
    _load_user_accounts()
except Exception as e:
    print(f"[UserDB] Could not load accounts: {e}")


# =============================================================================
# SESSION STORAGE (in-memory + SQLite for persistence)
# =============================================================================

_sessions = {}  # token -> {user_id, email, name, created_at, firebase_uid}
_users_cache = {}  # user_id -> full user data (merged from memory + Firebase)

# Load sessions from SQLite on startup (gracefully skip if DB fails)
try:
    conn = _get_user_db()
    rows = conn.execute('SELECT token, user_id, email, name, created_at, onboarding_complete, source FROM sessions').fetchall()
    conn.close()
    for row in rows:
        _sessions[row[0]] = {
            'user_id': row[1],
            'email': row[2],
            'name': row[3],
            'created_at': row[4],
            'onboarding_complete': bool(row[5]),
            'source': row[6],
        }
except Exception as e:
    print(f"[UserDB] Could not load sessions: {e}")


# =============================================================================
# SIMPLE EMAIL/PASSWORD AUTH
# =============================================================================

# In-memory user accounts: email -> {password_hash, uid, name}
# Loaded from SQLite at startup


def hash_password(password, salt=None):
    """Hash a password with salt."""
    import hmac
    if salt is None:
        salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + ':' + hashed.hex()


def verify_password(password, stored):
    """Verify a password against its hash."""
    try:
        salt_hex, hash_hex = stored.split(':')
        salt = bytes.fromhex(salt_hex)
        expected = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()
        return hmac.compare_digest(expected, hash_hex)
    except:
        return False


def create_session_token():
    return hashlib.sha256((str(uuid.uuid4()) + str(time.time())).encode()).hexdigest()[:32]


def get_or_create_demo_user():
    """Demo user with pre-seeded data — no Firebase needed."""
    global DEMO_TOKEN, _users_cache
    if DEMO_TOKEN is None:
        DEMO_TOKEN = create_session_token()
        uid = 'demo-user'
        _sessions[DEMO_TOKEN] = {
            'user_id': uid,
            'email': 'demo@example.com',
            'name': 'Demo User',
            'created_at': time.time(),
            'onboarding_complete': True,
            'source': 'demo',
        }
        _users_cache[uid] = _get_demo_user_data(uid)
    return DEMO_TOKEN


def _get_demo_user_data(uid):
    """Rich seed data for demo user."""
    return {
        'profile': {
            'name': 'Demo User',
            'email': 'demo@example.com',
            'briefing_style': 'balanced',
            'working_hours': '9am-6pm IST',
            'current_project': {'name': 'Building an AI productivity app', 'stage': 'building'},
            'people': [
                {'name': 'Alex Chen', 'context': 'Tech mentor, helps with system design', 'status': 'follows up weekly'},
                {'name': 'Jordan Lee', 'context': 'Co-founder, handles product roadmap', 'status': 'waiting on my input'},
            ],
            'weekly_goals': 'Ship user auth\nReview Q2 roadmap\nDemo to 3 beta users',
        },
        'memory': {
            'alex_context': {'key': 'alex_context', 'value': {'name': 'Alex Chen', 'context': 'Tech mentor', 'topic': 'system design review', 'status': 'active'}, 'confidence': 0.95, 'source': 'chat', 'updated_at': '2026-04-01'},
            'jordan_context': {'key': 'jordan_context', 'value': {'name': 'Jordan Lee', 'context': 'Co-founder', 'topic': 'product roadmap', 'status': 'waiting_on_me'}, 'confidence': 0.9, 'source': 'chat', 'updated_at': '2026-04-01'},
            'current_project': {'key': 'current_project', 'value': {'name': 'AI Productivity App', 'stage': 'building'}, 'confidence': 0.95, 'source': 'explicit', 'updated_at': '2026-04-01'},
            'user_preferences': {'key': 'user_preferences', 'value': {'briefing_style': 'balanced', 'communication': 'direct'}, 'confidence': 0.9, 'source': 'explicit', 'updated_at': '2026-04-01'},
        },
        'tasks': [
            {'id': 1, 'title': 'Ship user authentication', 'description': 'OAuth + session management', 'status': 'in_progress', 'priority': 'high', 'deadline': '2026-04-08T18:00:00+05:30'},
            {'id': 2, 'title': 'Review Q2 product roadmap with Jordan', 'description': 'Jordan sent draft on April 3', 'status': 'pending', 'priority': 'high', 'deadline': '2026-04-09T12:00:00+05:30'},
            {'id': 3, 'title': 'Demo to 3 beta users', 'description': 'Get feedback on core flow', 'status': 'pending', 'priority': 'medium', 'deadline': '2026-04-10T18:00:00+05:30'},
            {'id': 4, 'title': 'System design review with Alex', 'description': 'Architecture decisions for scale', 'status': 'pending', 'priority': 'medium', 'deadline': '2026-04-11T15:00:00+05:30'},
            {'id': 5, 'title': 'Write API documentation', 'description': 'REST endpoints', 'status': 'pending', 'priority': 'low'},
            {'id': 6, 'title': 'Deploy to production', 'description': 'Cloud Run + custom domain', 'status': 'done', 'priority': 'high', 'deadline': '2026-04-01T18:00:00+05:30'},
        ],
        'cal_events': [
            {'id': 'evt1', 'summary': 'Team standup', 'start': '2026-04-05T10:00:00+05:30', 'end': '2026-04-05T10:30:00+05:30', 'is_all_day': False, 'location': 'Zoom', 'attendees': ['team@company.com'], 'description': 'Daily sync'},
            {'id': 'evt2', 'summary': 'System design review with Alex', 'start': '2026-04-05T15:00:00+05:30', 'end': '2026-04-05T16:00:00+05:30', 'is_all_day': False, 'location': 'Google Meet', 'attendees': ['alex@company.com'], 'description': 'Architecture decisions'},
            {'id': 'evt3', 'summary': 'Product roadmap review', 'start': '2026-04-07T14:00:00+05:30', 'end': '2026-04-07T15:00:00+05:30', 'is_all_day': False, 'location': 'Zoom', 'attendees': ['jordan@company.com'], 'description': 'Q2 planning with Jordan'},
        ],
        'email_results': [
            {'id': 'em1', 'from': 'Alex Chen <alex@company.com>', 'subject': 'Re: Architecture decision', 'date': '2026-04-04', 'snippet': 'Thanks for the detailed write-up. A few thoughts on the caching strategy...'},
            {'id': 'em2', 'from': 'Jordan Lee <jordan@company.com>', 'subject': 'Product roadmap draft', 'date': '2026-04-03', 'snippet': 'Hi! Attached is the draft roadmap for Q2. Would love your thoughts before Friday...'},
        ],
        'google_data': None,  # Populated when Firebase user signs in
    }


def get_user_data(uid):
    """Get user data from cache, Firebase, or demo data."""
    if uid in _users_cache:
        return _users_cache[uid]

    # Try Firebase Firestore
    if firebase_initialized and fb:
        fb_data = fb.get_user_firestore_data(uid)
        if fb_data:
            _users_cache[uid] = fb_data
            return fb_data

    # Demo user
    if uid == 'demo-user':
        data = _get_demo_user_data(uid)
        _users_cache[uid] = data
        return data

    return None


def save_user_data(uid, data):
    """Save user data to cache and Firebase."""
    _users_cache[uid] = data

    if firebase_initialized and fb:
        fb.save_user_firestore_data(uid, data)

    return True


def get_current_user():
    """Get current user from request auth."""
    auth_header = request.headers.get('Authorization', '')

    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return _sessions.get(token)

    cookie_token = request.cookies.get('cortex_token')
    if cookie_token:
        return _sessions.get(cookie_token)

    # Demo token fallback (DEMO_MODE must also be set)
    if DEMO_MODE and DEMO_TOKEN:
        return _sessions.get(DEMO_TOKEN)

    return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# PAGE ROUTES
# =============================================================================

@app.route('/')
def index():
    # In demo mode, skip straight to onboarding
    if DEMO_MODE:
        return redirect('/onboarding')
    user = get_current_user()
    if user and user.get('onboarding_complete'):
        return redirect('/dashboard')
    elif user:
        return redirect('/onboarding')
    return redirect('/login')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/onboarding')
def onboarding_page():
    return render_template('onboarding.html')


@app.route('/dashboard')
def dashboard_page():
    user = get_current_user()
    if not user:
        return redirect('/login')
    return render_template('dashboard.html')


# =============================================================================
# AUTH API ENDPOINTS
# =============================================================================

@app.route('/api/auth/session', methods=['POST'])
def create_session():
    """
    Create a session. Supports:
    1. Email + password login (always works)
    2. Demo mode (no auth needed)
    """
    global _users_cache

    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    # -------------------------------------------------------------------------
    # PATH 1: Email + Password Login (always works)
    # -------------------------------------------------------------------------
    if email and password:
        if email not in _user_accounts:
            return jsonify({'error': 'No account found with this email. Sign up first.'}), 401

        account = _user_accounts[email]
        if not verify_password(password, account['password_hash']):
            return jsonify({'error': 'Incorrect password. Try again.'}), 401

        uid = account['uid']
        name = account['name']

        # Get or create session
        token = create_session_token()
        _sessions[token] = {
            'user_id': uid,
            'email': email,
            'name': name,
            'created_at': time.time(),
            'onboarding_complete': True,
            'source': 'email',
        }

        # Ensure user data exists
        if uid not in _users_cache:
            _users_cache[uid] = {
                'profile': {'name': name, 'email': email, 'briefing_style': 'balanced'},
                'memory': {},
                'tasks': [],
                'cal_events': [],
                'email_results': [],
                'google_data': None,
            }

        # Persist session to SQLite
        _save_session(token, uid, email, name, time.time(), True, 'email')

        resp = jsonify({
            'token': token,
            'user': {'email': email, 'name': name},
            'needs_onboarding': False,
            'mode': 'email',
        })
        resp.set_cookie('cortex_token', token, httponly=True, samesite='Lax', max_age=86400 * 30)
        return resp

    # -------------------------------------------------------------------------
    # PATH 2: Demo mode (no credentials)
    # -------------------------------------------------------------------------
    if DEMO_MODE:
        token = get_or_create_demo_user()
        user = _sessions[token]
        resp = jsonify({
            'token': token,
            'user': {'email': user['email'], 'name': user['name']},
            'needs_onboarding': not user.get('onboarding_complete', True),
            'mode': 'demo',
        })
        resp.set_cookie('cortex_token', token, httponly=True, samesite='Lax', max_age=86400 * 30)
        return resp

    return jsonify({'error': 'Email and password are required'}), 400


@app.route('/api/auth/demo', methods=['POST'])
def create_demo_session():
    """Create demo session — always available."""
    token = get_or_create_demo_user()
    user = _sessions[token]
    resp = jsonify({
        'token': token,
        'user': {'email': user['email'], 'name': user['name']},
        'needs_onboarding': not user.get('onboarding_complete', True),
        'mode': 'demo',
    })
    resp.set_cookie('cortex_token', token, httponly=True, samesite='Lax', max_age=86400 * 30)
    return resp


@app.route('/api/auth/register', methods=['POST'])
def register_user():
    """Register a new user with email and password. Creates account and auto-logs in."""
    print(f"[REGISTER] Called — DEMO_MODE={DEMO_MODE}, firebase={firebase_initialized}")
    print(f"[REGISTER] _user_accounts type: {type(_user_accounts)}, len: {len(_user_accounts)}")
    print(f"[REGISTER] _sessions type: {type(_sessions)}, len: {len(_sessions)}")
    try:
        global _users_cache

        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        name = (data.get('name') or '').strip() or email.split('@')[0]

        print(f"[REGISTER] email={email}, name={name}")

        if not email or '@' not in email:
            return jsonify({'error': 'Please enter a valid email address'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        if email in _user_accounts:
            return jsonify({'error': 'An account with this email already exists'}), 409

        uid = hashlib.sha256(email.encode()).hexdigest()[:16]
        password_hash = hash_password(password)
        _user_accounts[email] = {
            'password_hash': password_hash,
            'uid': uid,
            'name': name,
            'created_at': time.time(),
        }

        _users_cache[uid] = {
            'profile': {'name': name, 'email': email, 'briefing_style': 'balanced'},
            'memory': {},
            'tasks': [],
            'cal_events': [],
            'email_results': [],
            'google_data': None,
        }

        token = create_session_token()
        _sessions[token] = {
            'user_id': uid,
            'email': email,
            'name': name,
            'created_at': time.time(),
            'onboarding_complete': True,
            'source': 'email',
        }

        # Persist to SQLite
        _save_user_account(email, password_hash, uid, name, time.time())
        _save_session(token, uid, email, name, time.time(), True, 'email')

        print(f"[REGISTER] Success: uid={uid}, sessions={len(_sessions)}")

        resp = jsonify({
            'token': token,
            'user': {'email': email, 'name': name},
            'needs_onboarding': False,
            'mode': 'email',
        })
        resp.set_cookie('cortex_token', token, httponly=True, samesite='Lax', max_age=86400 * 30)
        return resp, 201

    except Exception as e:
        import traceback
        print(f"[REGISTER] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_me():
    user = get_current_user()
    udata = get_user_data(user['user_id']) or {}

    profile = udata.get('profile', {})
    google_data = udata.get('google_data')

    return jsonify({
        'user_id': user['user_id'],
        'name': profile.get('name', user.get('name', '')),
        'email': profile.get('email', user.get('email', '')),
        'briefing_style': profile.get('briefing_style', 'balanced'),
        'working_hours': profile.get('working_hours'),
        'current_project': profile.get('current_project'),
        'people': profile.get('people', []),
        'weekly_goals': profile.get('weekly_goals'),
        'needs_onboarding': not user.get('onboarding_complete', False),
        'memory_count': len(udata.get('memory', {})),
        'task_count': len(udata.get('tasks', [])),
        'has_google_data': google_data is not None,
        'google_email_count': len(google_data.get('emails', [])) if google_data else 0,
        'google_calendar_count': len(google_data.get('calendar_events', [])) if google_data else 0,
        'mode': user.get('source', 'demo'),
    })


@app.route('/api/auth/onboarding', methods=['POST'])
@require_auth
def finish_onboarding():
    """Complete onboarding — profile data + auto-pull from Gmail/Calendar."""
    global _users_cache

    user = get_current_user()
    uid = user['user_id']
    profile = request.get_json() or {}

    name = profile.get('name', user.get('name', ''))
    user_email = profile.get('email', user.get('email', ''))
    people = profile.get('people', [])
    current_project = profile.get('current_project', {})
    weekly_goals = profile.get('weekly_goals', '')

    # Build initial user data
    user_data = {
        'profile': {
            'name': name,
            'email': user_email,
            'briefing_style': profile.get('briefing_style', 'balanced'),
            'preferred_name': profile.get('preferred_name'),
            'working_hours': profile.get('working_hours'),
            'people': people,
            'current_project': current_project,
            'weekly_goals': weekly_goals,
        },
        'memory': {},
        'tasks': [],
        'cal_events': [],
        'email_results': [],
        'google_data': None,
    }

    # Seed memory from onboarding
    user_data['memory']['user_profile'] = {
        'key': 'user_profile',
        'value': {'name': name, 'email': user_email},
        'confidence': 1.0, 'source': 'explicit', 'updated_at': datetime.now().isoformat()
    }
    user_data['memory']['current_project'] = {
        'key': 'current_project',
        'value': current_project,
        'confidence': 1.0, 'source': 'explicit', 'updated_at': datetime.now().isoformat()
    }

    # Seed tasks from weekly goals
    if weekly_goals:
        goal_lines = [l.strip() for l in weekly_goals.split('\n') if l.strip()]
        for i, goal in enumerate(goal_lines[:5]):
            user_data['tasks'].append({
                'id': i + 1,
                'title': goal,
                'description': 'From weekly goals',
                'status': 'pending',
                'priority': 'medium',
                'source': 'onboarding'
            })

    # -------------------------------------------------------------------------
    # AUTO-PULL: If Firebase user with Google tokens, pull Gmail + Calendar
    # -------------------------------------------------------------------------
    if firebase_initialized and fb and user.get('firebase_uid'):
        # Get stored OAuth tokens from Firestore
        oauth_tokens = fb.get_user_oauth_tokens(user['firebase_uid'])
        if oauth_tokens:
            google_data = fb.onboard_user_with_google_data(
                uid, oauth_tokens, user_email, name
            )
            user_data = google_data  # Full data from Google auto-pull

    # Mark onboarding done
    user['name'] = name
    user['onboarding_complete'] = True

    save_user_data(uid, user_data)

    return jsonify({'status': 'ok', 'name': name})


# =============================================================================
# CORTEX QUERY — NOW USES REAL USER DATA + GOOGLE AUTO-PULLED DATA
# =============================================================================

@app.route('/api/query', methods=['POST'])
def api_query():
    """Main Cortex query — tries ADK AI agent first, falls back to rules engine."""
    data = request.get_json() or {}
    user_message = (data.get('message') or '').strip()
    session_id = data.get('session_id', 'default')

    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401

    uid = user['user_id']
    udata = get_user_data(uid)
    if not udata:
        return jsonify({'error': 'User data not found'}), 500

    profile = udata.get('profile', {})
    name = profile.get('name', user.get('name', 'there'))
    people = profile.get('people', [])
    cal_events = udata.get('cal_events', [])
    email_results = udata.get('email_results', [])
    tasks = udata.get('tasks', [])
    google_data = udata.get('google_data')

    user_message_lower = user_message.lower()

    # ── Try ADK AI agent first ─────────────────────────────────────────────
    if get_cortex_agent() is not None:
        try:
            loop = None
            try:
                import asyncio
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            ai_response = loop.run_until_complete(
                call_ai_agent(user_message, udata, session_id)
            )
            if ai_response and ai_response.strip():
                return jsonify({
                    'response': ai_response.strip(),
                    'session_id': session_id,
                    'agent': 'cortex',
                    'user_id': uid,
                    'has_google_data': google_data is not None,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            print(f"[Query] AI agent error, falling back to rules: {e}")

    # ── Rules engine fallback ───────────────────────────────────────────────
    if any(k in user_message_lower for k in ['plate', 'today', 'morning', 'briefing', 'agenda']):
        response = build_morning_briefing(name, profile, tasks, cal_events, people, google_data)

    elif any(k in user_message for k in ['follow up', 'send email', 'email to', 'draft email']):
        response = build_email_draft(user_message, people, profile)

    elif 'remember' in user_message or 'memory' in user_message or 'what do you know' in user_message:
        response = build_memory_response(profile, udata.get('memory', {}))

    elif 'task' in user_message and any(k in user_message for k in ['show', 'list', 'what']):
        response = build_tasks_response(tasks)

    elif 'add' in user_message and 'task' in user_message:
        response = add_task_from_message(user_message, tasks, udata, uid)

    elif any(k in user_message for k in ['who am i', 'about me', 'my profile']):
        response = build_profile_response(name, profile, people)

    elif 'email' in user_message and any(k in user_message for k in ['show', 'recent', 'inbox']):
        response = build_email_summary(email_results, google_data)

    elif 'remind' in user_message or 'reminder' in user_message or ('call' in user_message and 'at' in user_message):
        response = build_reminder_response(user_message, tasks, udata, uid)

    elif any(k in user_message for k in ['hi', 'hello', 'hey', 'sup', 'yo']):
        response = f"Hey {name}! 👋 What are you working on today?"

    else:
        response = build_fallback_response(name, tasks, profile)

    return jsonify({
        'response': response,
        'session_id': session_id,
        'agent': 'cortex',
        'user_id': uid,
        'has_google_data': google_data is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/debug', methods=['GET'])
@app.route('/api/debug/<path:subpath>', methods=['GET'])
def debug_route(subpath=None):
    return jsonify({
        'DEMO_MODE': DEMO_MODE,
        'firebase_initialized': firebase_initialized,
        'adk_agent_available': get_cortex_agent() is not None,
        'user_accounts_count': len(_user_accounts),
        '_users_cache_count': len(_users_cache),
        'sessions_count': len(_sessions),
    })


# =============================================================================
# CORTEX AGENT — ADK-powered AI (lazy import, falls back to rules)
# =============================================================================
_cortex_agent = None

def get_cortex_agent():
    """ADK agent disabled - using rules engine fallback only."""
    global _cortex_agent
    # Disable ADK agent for now - using rules engine instead
    # The rules engine handles morning briefing, tasks, memory, etc.
    _cortex_agent = None
    return None


async def call_ai_agent(user_message, user_data, session_id):
    """Call the ADK Cortex agent. Returns response string or None."""
    agent = get_cortex_agent()
    if not agent:
        return None

    try:
        import os
        from google.adk.sessions import SessionService, InMemorySessionService
        from google.adk.runners import Runner
        import uuid

        # Use in-memory session service (no database needed for demo)
        session_service = InMemorySessionService()

        user_id = user_data.get('user_id', 'unknown')
        session_id_val = session_id or str(uuid.uuid4())

        # Create a session
        session_service.create_session(
            app_name='cortex',
            user_id=user_id,
            session_id=session_id_val,
        )

        runner = Runner(
            app_name='cortex',
            agent=agent,
            session_service=session_service,
        )

        # Run the agent
        session = session_service.create_session(
            app_name='cortex',
            user_id=user_id,
            session_id=session_id_val,
        )

        response = runner.run(
            user_id=user_id,
            session_id=session_id_val,
            message=user_message,
        )

        if response and response.text:
            return response.text
    except Exception as e:
        import traceback
        print(f"[Cortex Agent] Error: {e}")
        traceback.print_exc()
    return None


# =============================================================================
# DATA API — PER-USER
# =============================================================================

@app.route('/api/memory', methods=['GET'])
@require_auth
def api_memory_list():
    uid = get_current_user()['user_id']
    udata = get_user_data(uid)
    entries = list(udata.get('memory', {}).values()) if udata else []
    return jsonify({'memory': entries})


@app.route('/api/memory', methods=['POST'])
@require_auth
def api_memory_put():
    user = get_current_user()
    uid = user['user_id']
    udata = get_user_data(uid) or {}
    data = request.get_json() or {}
    key = data.get('key')

    if key:
        udata.setdefault('memory', {})[key] = {
            'key': key,
            'value': data.get('value', {}),
            'confidence': data.get('confidence', 0.9),
            'source': data.get('source', 'chat'),
            'updated_at': datetime.now().isoformat()
        }
        save_user_data(uid, udata)
        return jsonify({'result': udata['memory'][key]})

    return jsonify({'error': 'key required'}), 400


@app.route('/api/memory/<key>', methods=['GET'])
@require_auth
def api_memory_get(key):
    uid = get_current_user()['user_id']
    udata = get_user_data(uid)
    entry = udata.get('memory', {}).get(key) if udata else None
    if entry:
        return jsonify(entry)
    return jsonify({'error': f"Key '{key}' not found"}), 404


@app.route('/api/tasks', methods=['GET'])
@require_auth
def api_tasks_list():
    uid = get_current_user()['user_id']
    udata = get_user_data(uid)
    tasks = udata.get('tasks', []) if udata else []
    status = request.args.get('status')
    priority = request.args.get('priority')
    if status:
        tasks = [t for t in tasks if t.get('status') == status]
    if priority:
        tasks = [t for t in tasks if t.get('priority') == priority]
    return jsonify({'tasks': tasks})


@app.route('/api/tasks', methods=['POST'])
@require_auth
def api_tasks_create():
    user = get_current_user()
    uid = user['user_id']
    udata = get_user_data(uid) or {}
    data = request.get_json() or {}

    tasks = udata.setdefault('tasks', [])
    tid = max([t.get('id', 0) for t in tasks] or [0]) + 1
    task = {
        'id': tid,
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'status': 'pending',
        'priority': data.get('priority', 'medium'),
        'deadline': data.get('deadline'),
        'source': 'manual'
    }
    tasks.append(task)
    save_user_data(uid, udata)
    return jsonify({'task': task}), 201


@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
@require_auth
def api_tasks_update(task_id):
    user = get_current_user()
    uid = user['user_id']
    udata = get_user_data(uid) or {}
    data = request.get_json() or {}

    for task in udata.get('tasks', []):
        if task.get('id') == task_id:
            for k in ['status', 'title', 'description', 'priority', 'deadline']:
                if k in data:
                    task[k] = data[k]
            save_user_data(uid, udata)
            return jsonify({'task': task})

    return jsonify({'error': f'Task {task_id} not found'}), 404


@app.route('/api/calendar/today', methods=['GET'])
@require_auth
def api_calendar_today():
    uid = get_current_user()['user_id']
    udata = get_user_data(uid)
    events = udata.get('cal_events', []) if udata else []
    google_data = udata.get('google_data')

    # If Firebase user has Google data, supplement with it
    if google_data:
        g_events = google_data.get('calendar_events', [])
        # Merge, dedupe by id
        event_ids = {e['id'] for e in events}
        for e in g_events:
            if e['id'] not in event_ids:
                events.append(e)

    return jsonify({'events': events, 'date': datetime.now().strftime('%Y-%m-%d')})


@app.route('/api/email/search', methods=['GET'])
@require_auth
def api_email_search():
    uid = get_current_user()['user_id']
    udata = get_user_data(uid)
    q = request.args.get('q', '').lower()
    results = udata.get('email_results', []) if udata else []
    google_data = udata.get('google_data')

    # Supplement with Google-pulled emails
    if google_data:
        g_emails = google_data.get('emails', [])
        for e in g_emails:
            if e not in results:
                results.append(e)

    if q:
        results = [e for e in results if q in e.get('subject', '').lower() or q in e.get('from', '').lower()]
    return jsonify({'results': results})


@app.route('/api/email/draft', methods=['POST'])
@require_auth
def api_email_draft():
    data = request.get_json() or {}
    return jsonify({'draft': {
        'draft_id': str(uuid.uuid4()),
        'to': data.get('to', ''),
        'subject': data.get('subject', ''),
        'status': 'Draft created — awaiting approval'
    }})


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'agent': 'cortex',
        'mode': 'demo' if DEMO_MODE else 'production',
        'firebase': firebase_initialized,
        'multi_user': True,
        'auto_pull': 'gmail_calendar' if firebase_initialized else 'demo_mode',
        'user_accounts_count': len(_user_accounts),
        'sessions_count': len(_sessions),
        'timestamp': datetime.now().isoformat()
    })


# =============================================================================
# RESPONSE BUILDERS
# =============================================================================

def build_morning_briefing(name, profile, tasks, cal_events, people, google_data):
    pending = [t for t in tasks if t.get('status') == 'pending']
    urgent = [t for t in pending if t.get('priority') == 'urgent']
    high = [t for t in pending if t.get('priority') == 'high']
    g_events = google_data.get('calendar_events', []) if google_data else []
    g_emails = google_data.get('emails', []) if google_data else []

    lines = [f"Good morning, {name}! Here's your briefing for {datetime.now().strftime('%B %d, %Y')}:"]
    lines.append("")

    # Calendar events (from Google Calendar auto-pull)
    all_events = list(cal_events) + list(g_events)
    if all_events:
        lines.append("📅 TODAY'S SCHEDULE:")
        for e in all_events[:5]:
            lines.append(f"  • {e.get('summary', '(No title)')}")
            if e.get('location'):
                lines[-1] += f" 📍 {e['location']}"
            if e.get('attendees'):
                lines[-1] += f" with {', '.join(e['attendees'][:2])}"
        lines.append("")

    # Auto-detected from Gmail
    if g_emails:
        unread_important = [e for e in g_emails if 'unread' in str(e.get('label_ids', [])).lower() or e.get('snippet')]
        if unread_important:
            lines.append(f"📧 EMAILS (auto-imported from Gmail, {len(unread_important)} recent):")
            for e in unread_important[:3]:
                lines.append(f"  • {e.get('from', '').split('<')[0].strip()}: \"{e.get('subject', '')[:50]}\"")
            lines.append("")

    # Priority tasks
    if urgent or high:
        lines.append("🔴 TOP PRIORITIES:")
        for t in (urgent + high)[:3]:
            deadline = f" — by {t.get('deadline', '')[:10]}" if t.get('deadline') else ""
            lines.append(f"  🔴 {t.get('title', '')}{deadline}")
        lines.append("")

    # People following up
    if people:
        waiting = [p for p in people if 'wait' in p.get('status', '').lower()]
        if waiting:
            lines.append("👥 FOLLOWING UP:")
            for p in waiting[:2]:
                lines.append(f"  • {p.get('name', '')}: {p.get('context', '')}")
            lines.append("")

    # Project
    project = profile.get('current_project', {})
    if project and project.get('name'):
        lines.append(f"💼 PROJECT: {project['name']} ({project.get('stage', '')})")

    if pending:
        lines.append(f"\n📋 {len(pending)} pending tasks. Say 'show my tasks' for the full list.")

    lines.append("\nWhat would you like to focus on?")
    return "\n".join(lines)


def build_email_summary(email_results, google_data):
    all_emails = list(email_results)
    if google_data:
        all_emails.extend(google_data.get('emails', []))

    if not all_emails:
        return "No emails found."

    lines = [f"📧 Recent Emails ({len(all_emails)}):"]
    for e in all_emails[:5]:
        sender = e.get('from', 'Unknown')
        if '<' in sender:
            sender = sender.split('<')[0].strip()
        lines.append(f"  • {sender}: \"{e.get('subject', '')}\"")
        if e.get('snippet'):
            lines[-1] += f" — {e['snippet'][:60]}"
    return "\n".join(lines)


def build_tasks_response(tasks):
    if not tasks:
        return "No tasks yet! Say 'add a task to [description]' to create one."

    pending = [t for t in tasks if t.get('status') == 'pending']
    done = [t for t in tasks if t.get('status') == 'done']

    lines = [f"📋 Your tasks ({len(pending)} pending, {len(done)} done):"]
    if pending:
        for priority in ['urgent', 'high', 'medium', 'low']:
            pts = [t for t in pending if t.get('priority') == priority]
            if pts:
                emoji = {'urgent': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '⚪'}.get(priority, '•')
                lines.append(f"\n{emoji} {priority.upper()}:")
                for t in pts:
                    deadline = f" [{t.get('deadline', '')[:10]}]" if t.get('deadline') else ""
                    lines.append(f"  • {t.get('title', '')}{deadline}")
    if done:
        lines.append(f"\n✅ Done ({len(done)}): {', '.join(t.get('title', '')[:40] for t in done[:3])}")
    return "\n".join(lines)


def add_task_from_message(msg, tasks, udata, uid):
    import re
    match = re.search(r'task to ([^\?]+)', msg, re.IGNORECASE)
    if match:
        title = match.group(1).strip().capitalize()
        tid = max([t.get('id', 0) for t in tasks] or [0]) + 1
        new_task = {'id': tid, 'title': title, 'description': 'Added via chat', 'status': 'pending', 'priority': 'medium', 'source': 'chat'}
        udata.setdefault('tasks', []).append(new_task)
        save_user_data(uid, udata)
        return f"✅ Task added: '{title}' — priority: medium. Say 'show my tasks' to see all."
    return "I didn't catch the task. Try: 'add a task to [description]'"


def build_memory_response(profile, memory):
    if not profile.get('name'):
        return "I don't have any memory of you yet. Complete onboarding to set up your profile!"

    lines = [f"Here's what I know about you, {profile.get('name', '')}:"]
    if profile.get('current_project', {}).get('name'):
        lines.append(f"\n💼 Project: {profile['current_project']['name']} ({profile['current_project'].get('stage', '')})")
    if profile.get('working_hours'):
        lines.append(f"⏰ Working: {profile['working_hours']}")

    entries = list(memory.values())
    if entries:
        lines.append(f"\n🧠 {len(entries)} memory entries:")
        for e in entries[:5]:
            val = e.get('value', {})
            if isinstance(val, dict):
                key_facts = ', '.join(f"{k}: {v}" for k, v in list(val.items())[:3])
            else:
                key_facts = str(val)[:100]
            lines.append(f"  • {e.get('key', '')}: {key_facts}")

    return "\n".join(lines)


def build_profile_response(name, profile, people):
    lines = [f"You're {name}!"]
    if profile.get('email'):
        lines.append(f"Email: {profile['email']}")
    project = profile.get('current_project', {})
    if project and project.get('name'):
        lines.append(f"Working on: {project['name']} ({project.get('stage', '')})")
    if people:
        lines.append(f"\n{len(people)} people in your network.")
    return "\n".join(lines)


def build_reminder_response(msg, tasks, udata, uid):
    """Handle reminder/schedule requests."""
    import re
    import datetime

    # Match "remind me to X at Y" or "call X at Y"
    call_match = re.search(r'(?:call|remind|contact)\s+(\w+)\s+(?:at|@)\s*(\d{1,2})\s*(?:am|pm)?', msg, re.IGNORECASE)
    if call_match:
        person = call_match.group(1).capitalize()
        hour = int(call_match.group(2))
        tid = max([t.get('id', 0) for t in tasks] or [0]) + 1
        # Default to 8am if not specified with am/pm
        new_task = {
            'id': tid,
            'title': f"Call {person}",
            'description': f'Reminder set via chat',
            'status': 'pending',
            'priority': 'high',
            'source': 'chat'
        }
        udata.setdefault('tasks', []).append(new_task)
        save_user_data(uid, udata)
        return f"🔔 Reminder set: Call {person} at {hour}:00. I've added it to your high-priority tasks."

    # General reminder
    reminder_match = re.search(r'remind(?:er)?\s+(?:me\s+)?(?:to\s+)?(.+)', msg, re.IGNORECASE)
    if reminder_match:
        title = reminder_match.group(1).strip().capitalize()
        tid = max([t.get('id', 0) for t in tasks] or [0]) + 1
        new_task = {
            'id': tid,
            'title': f"Reminder: {title}",
            'description': 'Added via chat',
            'status': 'pending',
            'priority': 'medium',
            'source': 'chat'
        }
        udata.setdefault('tasks', []).append(new_task)
        save_user_data(uid, udata)
        return f"🔔 Reminder saved: '{title}'. Check your tasks for details."

    return "I didn't catch the reminder. Try: 'remind me to call atharva at 8am'"


def build_fallback_response(name, tasks, profile):
    """Dynamic fallback when no rule matched — checks what's relevant."""
    suggestions = []

    pending_tasks = [t for t in tasks if t.get('status') != 'done']
    if pending_tasks:
        suggestions.append("check your task list")
    if profile.get('current_project', {}).get('name'):
        suggestions.append("discuss your project")
    if not profile.get('name') or profile.get('name') == 'there':
        suggestions.append("complete your profile")
    else:
        suggestions.append("set a reminder")
        suggestions.append("ask about your schedule")

    suggestion_text = "\n• ".join(suggestions)
    return f"Hey {name}! I'm here to help. Try: {suggestion_text}"


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting Cortex — Firebase: {firebase_initialized}, Demo: {DEMO_MODE}")
    app.run(host='0.0.0.0', port=port, debug=debug)
