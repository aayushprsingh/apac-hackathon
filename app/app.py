"""
Cortex Flask App — Multi-User with Auth
Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

Auth: Firebase Auth (Google OAuth) when configured, demo token fallback otherwise.
Data isolation: Per-user in-memory store + PostgreSQL when configured.
"""

import os
import json
import uuid
import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', os.urandom(32))
CORS(app)

DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'

# ============================================================================
# SIMPLE TOKEN-BASED AUTH (works without Firebase)
# Sessions stored in memory — production: use Redis or DB
# ============================================================================

_sessions = {}  # token -> {user_id, email, name, created_at}
_users = {}     # user_id -> {profile, memory, tasks, ...}

DEMO_TOKEN = None  # Set on first demo request


def create_session_token():
    """Create a simple session token."""
    return hashlib.sha256((str(uuid.uuid4()) + str(time.time())).encode()).hexdigest()[:32]


def get_or_create_demo_user():
    """Get or create the demo user for demo mode."""
    global DEMO_TOKEN
    if DEMO_TOKEN is None:
        DEMO_TOKEN = create_session_token()
        _sessions[DEMO_TOKEN] = {
            'user_id': 'demo-user',
            'email': 'demo@example.com',
            'name': 'Demo User',
            'created_at': time.time(),
            'onboarding_complete': True,
        }
        _users['demo-user'] = _get_demo_user_data('demo-user')
    return DEMO_TOKEN


def _get_demo_user_data(uid):
    """Seed data for demo user."""
    return {
        'profile': {
            'name': 'Demo User',
            'email': 'demo@example.com',
            'briefing_style': 'balanced',
            'working_hours': '9am-6pm',
            'current_project': {'name': 'Building a productivity app', 'stage': 'building'},
            'people': [
                {'name': 'Alex Chen', 'context': 'Tech mentor, helping with system design', 'status': 'follows up weekly'},
                {'name': 'Jordan Lee', 'context': 'Co-founder, handles product', 'status': 'waiting on product roadmap'},
            ],
            'weekly_goals': 'Ship user auth\nReview Q2 roadmap\nDemo to 3 users',
            'pending_followups': 'Alex — system design review due Friday\nJordan — product roadmap by Wednesday',
        },
        'memory': {
            'alex_context': {'key': 'alex_context', 'value': {'name': 'Alex Chen', 'context': 'Tech mentor', 'topic': 'system design', 'status': 'active'}, 'confidence': 0.95, 'source': 'chat', 'updated_at': '2026-04-01'},
            'jordan_context': {'key': 'jordan_context', 'value': {'name': 'Jordan Lee', 'context': 'Co-founder', 'topic': 'product roadmap', 'status': 'waiting_on_me'}, 'confidence': 0.9, 'source': 'chat', 'updated_at': '2026-04-01'},
            'current_project': {'key': 'current_project', 'value': {'name': 'Productivity App MVP', 'stage': 'building'}, 'confidence': 0.95, 'source': 'explicit', 'updated_at': '2026-04-01'},
            'user_preferences': {'key': 'user_preferences', 'value': {'briefing_style': 'balanced', 'communication': 'direct'}, 'confidence': 0.9, 'source': 'explicit', 'updated_at': '2026-04-01'},
            'weekly_goals': {'key': 'weekly_goals', 'value': {'goals': ['Ship user auth', 'Review Q2 roadmap', 'Demo to 3 users']}, 'confidence': 0.9, 'source': 'explicit', 'updated_at': '2026-04-01'},
        },
        'tasks': [
            {'id': 1, 'title': 'Ship user authentication', 'description': 'OAuth + session management', 'status': 'in_progress', 'priority': 'high', 'deadline': '2026-04-08T18:00:00+05:30'},
            {'id': 2, 'title': 'Review Q2 product roadmap', 'description': 'With Jordan on product direction', 'status': 'pending', 'priority': 'high', 'deadline': '2026-04-09T12:00:00+05:30'},
            {'id': 3, 'title': 'Demo to 3 beta users', 'description': 'Get feedback on core flow', 'status': 'pending', 'priority': 'medium', 'deadline': '2026-04-10T18:00:00+05:30'},
            {'id': 4, 'title': 'System design review with Alex', 'description': 'Architecture decisions for scale', 'status': 'pending', 'priority': 'medium', 'deadline': '2026-04-11T15:00:00+05:30'},
            {'id': 5, 'title': 'Write API documentation', 'description': 'For the REST endpoints', 'status': 'pending', 'priority': 'low', 'deadline': None},
            {'id': 6, 'title': 'Set up analytics pipeline', 'description': 'Track user events and retention', 'status': 'blocked', 'priority': 'medium', 'deadline': '2026-04-14T18:00:00+05:30'},
            {'id': 7, 'title': 'Deploy to production', 'description': 'Cloud Run + custom domain', 'status': 'done', 'priority': 'high', 'deadline': '2026-04-01T18:00:00+05:30'},
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
    }


def get_current_user():
    """Extract user from request token."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return _sessions.get(token)

    cookie_token = request.cookies.get('cortex_token')
    if cookie_token:
        return _sessions.get(cookie_token)

    if DEMO_MODE and DEMO_TOKEN:
        return _sessions.get(DEMO_TOKEN)

    return None


def require_auth(f):
    """Decorator: require valid auth token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        request.cortex_user = user
        return f(*args, **kwargs)
    return decorated


def get_user_data():
    """Get the current user's data store."""
    user = get_current_user()
    if not user:
        return None
    uid = user['user_id']
    if uid not in _users:
        _users[uid] = _get_demo_user_data(uid) if uid == 'demo-user' else {'profile': {}, 'memory': {}, 'tasks': [], 'cal_events': [], 'email_results': []}
    return _users[uid]


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Root → redirect based on auth state."""
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


@app.route('/memory')
def memory_page():
    return redirect('/dashboard')


@app.route('/tasks')
def tasks_page():
    return redirect('/dashboard')


# ============================================================================
# AUTH API ENDPOINTS
# ============================================================================

@app.route('/api/auth/session', methods=['POST'])
def create_session():
    """
    Create a session from Firebase ID token, or create demo session.
    Returns session token + onboarding status.
    """
    global DEMO_TOKEN

    data = request.get_json() or {}
    id_token = data.get('id_token')

    if id_token and not DEMO_MODE:
        # Verify Firebase token (skip in demo mode)
        try:
            import firebase_admin
            from firebase_admin import auth
            decoded = auth.verify_id_token(id_token)
            email = decoded.get('email')
            name = decoded.get('name', email.split('@')[0])
        except:
            # Firebase not configured — create session from email
            email = data.get('email', 'unknown@example.com')
            name = data.get('name', email.split('@')[0])

        uid = hashlib.sha256(email.encode()).hexdigest()[:16]
        token = create_session_token()

        # Check if onboarding already done
        onboarding_done = uid in _users and bool(_users[uid].get('profile', {}).get('name'))

        _sessions[token] = {
            'user_id': uid,
            'email': email,
            'name': name,
            'created_at': time.time(),
            'onboarding_complete': onboarding_done,
        }

        resp = jsonify({
            'token': token,
            'user': {'email': email, 'name': name},
            'needs_onboarding': not onboarding_done,
        })
        resp.set_cookie('cortex_token', token, httponly=True, samesite='Lax', max_age=86400 * 30)
        return resp

    # Demo mode
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


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_me():
    """Get current user profile."""
    udata = get_user_data()
    user = request.cortex_user
    profile = udata.get('profile', {}) if udata else {}

    # Get first memory entry as a sample
    memory_entries = list(udata.get('memory', {}).values()) if udata else []
    first_memory = memory_entries[0] if memory_entries else None

    return jsonify({
        'user_id': user['user_id'],
        'name': profile.get('name', user.get('name', '')),
        'email': profile.get('email', user.get('email', '')),
        'briefing_style': profile.get('briefing_style', 'balanced'),
        'working_hours': profile.get('working_hours'),
        'current_project': profile.get('current_project'),
        'people': profile.get('people', []),
        'weekly_goals': profile.get('weekly_goals'),
        'pending_followups': profile.get('pending_followups'),
        'needs_onboarding': not user.get('onboarding_complete', False),
        'memory_count': len(udata.get('memory', {})) if udata else 0,
        'task_count': len(udata.get('tasks', [])) if udata else 0,
    })


@app.route('/api/auth/onboarding', methods=['POST'])
@require_auth
def finish_onboarding():
    """Save onboarding profile and seed user's memory + tasks."""
    user = request.cortex_user
    udata = get_user_data()
    if not udata:
        return jsonify({'error': 'User data not found'}), 500

    profile = request.get_json() or {}
    name = profile.get('name', '')
    email = profile.get('email', user.get('email', ''))
    people = profile.get('people', [])
    current_project = profile.get('current_project', {})
    weekly_goals = profile.get('weekly_goals', '')

    # Save profile
    udata['profile'] = {
        'name': name,
        'email': email,
        'briefing_style': profile.get('briefing_style', 'balanced'),
        'preferred_name': profile.get('preferred_name'),
        'working_hours': profile.get('working_hours'),
        'people': people,
        'current_project': current_project,
        'weekly_goals': weekly_goals,
        'pending_followups': profile.get('pending_followups', ''),
    }

    # Mark onboarding done
    user['name'] = name
    user['onboarding_complete'] = True

    # Seed memory from onboarding
    memory = udata['memory']
    memory['user_profile'] = {
        'key': 'user_profile',
        'value': {'name': name, 'email': email, 'briefing_style': profile.get('briefing_style')},
        'confidence': 1.0, 'source': 'explicit', 'updated_at': datetime.now().isoformat()
    }
    memory['current_project'] = {
        'key': 'current_project',
        'value': current_project,
        'confidence': 1.0, 'source': 'explicit', 'updated_at': datetime.now().isoformat()
    }
    memory['weekly_goals'] = {
        'key': 'weekly_goals',
        'value': {'goals': weekly_goals.split('\n') if weekly_goals else [], 'week_of': datetime.now().strftime('%Y-%m-%d')},
        'confidence': 0.95, 'source': 'explicit', 'updated_at': datetime.now().isoformat()
    }

    if people:
        memory['key_people'] = {
            'key': 'key_people',
            'value': {'people': people, 'count': len(people)},
            'confidence': 1.0, 'source': 'explicit', 'updated_at': datetime.now().isoformat()
        }

    if weekly_goals:
        # Parse and create tasks from goals
        goal_lines = [l.strip() for l in weekly_goals.split('\n') if l.strip()]
        for i, goal in enumerate(goal_lines[:5]):
            tid = max([t['id'] for t in udata['tasks']] or [0]) + i + 1
            udata['tasks'].append({
                'id': tid, 'title': goal, 'description': 'From weekly goals',
                'status': 'pending', 'priority': 'medium', 'deadline': None
            })

    # Seed sample calendar + email for demo
    udata['cal_events'] = [
        {'id': 'evt1', 'summary': f'{name}\'s Day', 'start': datetime.now().strftime('%Y-%m-%d') + 'T09:00:00+05:30', 'end': datetime.now().strftime('%Y-%m-%d') + 'T17:00:00+05:30', 'is_all_day': False, 'location': '', 'attendees': [], 'description': 'Your workday'},
    ]

    udata['email_results'] = [
        {'id': 'em1', 'from': f'System <noreply@{email.split("@")[1]}', 'subject': f'Welcome to Cortex, {name}!', 'date': datetime.now().strftime('%Y-%m-%d'), 'snippet': 'Your personal AI assistant is ready. Start by asking "What\'s on my plate today?"'},
    ]

    return jsonify({'status': 'ok', 'name': name})


@app.route('/api/auth/demo', methods=['POST'])
def create_demo_session():
    """Create demo session without Firebase — for hackathon demo."""
    return create_session()


# ============================================================================
# CORTEX QUERY — NOW PER-USER
# ============================================================================

@app.route('/api/query', methods=['POST'])
def api_query():
    """Main Cortex query — uses authenticated user's data."""
    data = request.get_json() or {}
    user_message = (data.get('message') or '').lower()
    session_id = data.get('session_id', 'default')

    udata = get_user_data()
    if not udata:
        return jsonify({'error': 'Authentication required'}), 401

    profile = udata.get('profile', {})
    name = profile.get('name', 'there')
    briefing_style = profile.get('briefing_style', 'balanced')
    project = profile.get('current_project', {})
    people = profile.get('people', [])
    cal_events = udata.get('cal_events', [])
    email_results = udata.get('email_results', [])
    tasks = udata.get('tasks', [])

    # Build response based on query
    if any(k in user_message for k in ['plate', 'today', 'morning', 'briefing', 'agenda']):
        response = build_morning_briefing(name, briefing_style, tasks, cal_events, people, project)

    elif any(k in user_message for k in ['follow up', 'send email', 'email to', 'draft email', 'send an email']):
        response = build_email_draft(user_message, people, project)

    elif 'remember' in user_message or 'memory' in user_message or 'what do you know' in user_message:
        response = build_memory_response(profile, udata.get('memory', {}))

    elif 'task' in user_message and any(k in user_message for k in ['show', 'list', 'what']):
        response = build_tasks_response(tasks)

    elif 'add' in user_message and 'task' in user_message:
        response = add_task_from_message(user_message, tasks, udata)
        tasks_marked_changed = True

    elif any(k in user_message for k in ['who am i', 'about me', 'my profile', 'what do you know about me']):
        response = build_profile_response(name, profile, project, people)

    elif 'schedule' in user_message or 'calendar' in user_message or 'meeting' in user_message:
        response = build_calendar_response(cal_events)

    else:
        response = f"Hey {name}! I'm Cortex — your persistent productivity assistant. Try asking:\n• \"What's on my plate today?\"\n• \"What do you remember about me?\"\n• \"Show my tasks\"\n• \"Add a task to [description]\""

    return jsonify({
        'response': response,
        'session_id': session_id,
        'agent': 'cortex',
        'user_id': get_current_user()['user_id'] if get_current_user() else None,
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# DATA API — NOW PER-USER
# ============================================================================

@app.route('/api/memory', methods=['GET'])
@require_auth
def api_memory_list():
    udata = get_user_data()
    entries = list(udata.get('memory', {}).values()) if udata else []
    return jsonify({'memory': entries})


@app.route('/api/memory', methods=['POST'])
@require_auth
def api_memory_put():
    udata = get_user_data()
    data = request.get_json() or {}
    key = data.get('key')
    if key:
        udata['memory'][key] = {
            'key': key,
            'value': data.get('value', {}),
            'confidence': data.get('confidence', 0.9),
            'source': data.get('source', 'chat'),
            'updated_at': datetime.now().isoformat()
        }
        return jsonify({'result': udata['memory'][key]})
    return jsonify({'error': 'key required'}), 400


@app.route('/api/memory/<key>', methods=['GET'])
@require_auth
def api_memory_get(key):
    udata = get_user_data()
    entry = udata.get('memory', {}).get(key)
    if entry:
        return jsonify(entry)
    return jsonify({'error': f"Key '{key}' not found"}), 404


@app.route('/api/tasks', methods=['GET'])
@require_auth
def api_tasks_list():
    udata = get_user_data()
    status = request.args.get('status')
    priority = request.args.get('priority')
    tasks = udata.get('tasks', [])
    if status:
        tasks = [t for t in tasks if t.get('status') == status]
    if priority:
        tasks = [t for t in tasks if t.get('priority') == priority]
    return jsonify({'tasks': tasks})


@app.route('/api/tasks', methods=['POST'])
@require_auth
def api_tasks_create():
    udata = get_user_data()
    data = request.get_json() or {}
    tid = max([t['id'] for t in udata['tasks']] or [0]) + 1
    task = {
        'id': tid,
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'status': 'pending',
        'priority': data.get('priority', 'medium'),
        'deadline': data.get('deadline'),
    }
    udata['tasks'].append(task)
    return jsonify({'task': task}), 201


@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
@require_auth
def api_tasks_update(task_id):
    udata = get_user_data()
    data = request.get_json() or {}
    for task in udata['tasks']:
        if task['id'] == task_id:
            for k in ['status', 'title', 'description', 'priority', 'deadline']:
                if k in data:
                    task[k] = data[k]
            return jsonify({'task': task})
    return jsonify({'error': f'Task {task_id} not found'}), 404


@app.route('/api/calendar/today', methods=['GET'])
@require_auth
def api_calendar_today():
    udata = get_user_data()
    return jsonify({'events': udata.get('cal_events', []), 'date': datetime.now().strftime('%Y-%m-%d')})


@app.route('/api/email/search', methods=['GET'])
@require_auth
def api_email_search():
    udata = get_user_data()
    q = request.args.get('q', '').lower()
    results = udata.get('email_results', [])
    if q:
        results = [e for e in results if q in e.get('subject', '').lower() or q in e.get('from', '').lower() or q in e.get('snippet', '').lower()]
    return jsonify({'results': results})


@app.route('/api/email/draft', methods=['POST'])
@require_auth
def api_email_draft():
    data = request.get_json() or {}
    draft = {
        'draft_id': str(uuid.uuid4()),
        'to': data.get('to', ''),
        'subject': data.get('subject', ''),
        'status': 'Draft created — awaiting approval'
    }
    return jsonify({'draft': draft})


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'agent': 'cortex',
        'mode': 'demo' if DEMO_MODE else 'production',
        'multi_user': True,
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# RESPONSE BUILDERS
# ============================================================================

def build_morning_briefing(name, style, tasks, cal_events, people, project):
    pending = [t for t in tasks if t['status'] == 'pending']
    urgent = [t for t in pending if t['priority'] == 'urgent']
    high = [t for t in pending if t['priority'] == 'high']
    medium = [t for t in pending if t['priority'] == 'medium']

    lines = [f"Good morning, {name}! Here's your briefing for {datetime.now().strftime('%B %d, %Y')}:"]
    lines.append("")

    if cal_events:
        lines.append("📅 TODAY'S SCHEDULE:")
        for e in cal_events[:5]:
            lines.append(f"  • {e['summary']}")
            if e.get('location'):
                lines[-1] += f" 📍 {e['location']}"
        lines.append("")

    if urgent or high:
        lines.append("📋 TOP PRIORITIES:")
        for t in (urgent + high)[:3]:
            deadline = f" — by {t.get('deadline', '')[:10]}" if t.get('deadline') else ""
            lines.append(f"  🔴 {t['title']}{deadline}")
        lines.append("")

    if people:
        waiting = [p for p in people if 'waiting' in p.get('status', '').lower()]
        if waiting:
            lines.append("👥 FOLLOWING UP:")
            for p in waiting[:2]:
                lines.append(f"  • {p['name']}: {p.get('context', '')} — {p.get('status', '')}")
            lines.append("")

    if project and project.get('name'):
        lines.append(f"💼 PROJECT: {project['name']} ({project.get('stage', '')})")

    if pending:
        lines.append(f"\n📋 {len(pending)} pending tasks total — say 'show my tasks' for full list")

    lines.append("\nWhat would you like to focus on?")
    return "\n".join(lines)


def build_email_draft(msg, people, project):
    person = None
    if people:
        for p in people:
            if p.get('name', '').lower() in msg:
                person = p
                break

    person_name = person.get('name', '[Name]') if person else 'them'
    context = person.get('context', 'your recent conversation') if person else 'your recent conversation'
    project_name = project.get('name', 'the project') if project else 'the project'

    return f"""✏️ DRAFT EMAIL — Review before sending:

To: {person.get('name', 'recipient')}@example.com
Subject: Re: {context.title()}

Hi {person_name.split()[0]},

Following up from {context}.

[Write your follow-up message here]

Let me know if you need anything from my side.

Best, [Your name]

---
Reply "send", "yes", or "go ahead" to confirm.
Reply "edit" to modify."""


def build_memory_response(profile, memory):
    if not profile.get('name'):
        return "I don't have any memory of you yet — you haven't completed onboarding. Go to /onboarding to set up your profile!"

    lines = [f"Here's what I know about you, {profile.get('name', '')}:"]
    if profile.get('current_project', {}).get('name'):
        lines.append(f"\n💼 Current project: {profile['current_project']['name']} ({profile['current_project'].get('stage', '')})")
    if profile.get('working_hours'):
        lines.append(f"⏰ Working hours: {profile['working_hours']}")
    if profile.get('briefing_style'):
        lines.append(f"📝 Briefing style: {profile['briefing_style']}")

    entries = list(memory.values())
    if entries:
        lines.append(f"\n🧠 Memory entries ({len(entries)} stored):")
        for e in entries[:5]:
            val = e.get('value', {})
            if isinstance(val, dict):
                key_facts = ', '.join(f"{k}: {v}" for k, v in list(val.items())[:3])
            else:
                key_facts = str(val)[:100]
            lines.append(f"  • {e['key']}: {key_facts}")

    return "\n".join(lines)


def build_tasks_response(tasks):
    if not tasks:
        return "No tasks yet! Say 'add a task to [description]' to create one."

    pending = [t for t in tasks if t['status'] == 'pending']
    done = [t for t in tasks if t['status'] == 'done']
    blocked = [t for t in tasks if t['status'] == 'blocked']

    lines = [f"📋 Your tasks ({len(pending)} pending, {len(done)} done):"]
    if pending:
        urgent = [t for t in pending if t['priority'] == 'urgent']
        high = [t for t in pending if t['priority'] == 'high']
        medium = [t for t in pending if t['priority'] == 'medium']
        low = [t for t in pending if t['priority'] == 'low']
        if urgent: lines.append(f"\n🔴 URGENT: {', '.join(t['title'] for t in urgent)}")
        if high: lines.append(f"\n🟠 HIGH: {', '.join(t['title'] for t in high)}")
        if medium: lines.append(f"\n🟡 MEDIUM: {', '.join(t['title'] for t in medium)}")
        if low: lines.append(f"\n⚪ LOW: {', '.join(t['title'] for t in low)}")
    if blocked:
        lines.append(f"\n⛔ BLOCKED: {', '.join(t['title'] for t in blocked)}")
    return "\n".join(lines)


def add_task_from_message(msg, tasks, udata):
    # Extract task description from message
    import re
    match = re.search(r'task to ([^\?]+)', msg, re.IGNORECASE)
    if match:
        title = match.group(1).strip().capitalize()
        tid = max([t['id'] for t in tasks] or [0]) + 1
        new_task = {'id': tid, 'title': title, 'description': 'Added via chat', 'status': 'pending', 'priority': 'medium'}
        udata['tasks'].append(new_task)
        return f"✅ Task added: '{title}' — priority: medium. Say 'show my tasks' to see all."
    return "I didn't catch the task. Try: 'add a task to [description]'"


def build_profile_response(name, profile, project, people):
    lines = [f"You're {name}!"]
    if profile.get('email'):
        lines.append(f"Email: {profile['email']}")
    if project and project.get('name'):
        lines.append(f"Working on: {project['name']} ({project.get('stage', '')})")
    if profile.get('working_hours'):
        lines.append(f"Working hours: {profile['working_hours']}")
    if people:
        lines.append(f"\n{len(people)} people in your network: {', '.join(p['name'] for p in people)}")
    return "\n".join(lines)


def build_calendar_response(cal_events):
    if not cal_events:
        return "No events scheduled today. Want me to add one? Say 'schedule a meeting tomorrow at 3pm'."
    lines = ["📅 Your schedule:"]
    for e in cal_events:
        lines.append(f"  • {e['summary']} — {e.get('location', 'No location')}")
    return "\n".join(lines)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting Cortex in {'DEMO' if DEMO_MODE else 'PRODUCTION'} mode — multi-user: True")
    app.run(host='0.0.0.0', port=port, debug=debug)
