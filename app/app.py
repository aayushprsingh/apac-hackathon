"""
Cortex Flask Web App (DEMO MODE)
In-memory version for immediate deployment demonstration.
Includes all functionality but uses in-memory storage instead of Cloud SQL.
For production: replace IN_MEMORY_* with real PostgreSQL/Firestore calls.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ============================================================================
# IN-MEMORY DEMO STORAGE (replace with PostgreSQL/Firestore in production)
# ============================================================================

DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'

# In-memory storage for demo
_memory_store = {
    'rahul_context': {'key': 'rahul_context', 'value': {'name': 'Rahul Sharma', 'relationship': 'investor', 'topic': '15% equity for ₹50L', 'last_contact': '2026-04-03', 'status': 'waiting_on_rahul', 'notes': 'Deadline was April 1 — 4 days overdue'}, 'confidence': 0.95, 'source': 'chat', 'updated_at': '2026-04-02T10:00:00+05:30'},
    'current_project': {'key': 'current_project', 'value': {'name': 'Bhooyam Ankuran Jal', 'stage': 'pre-launch', 'priority': 'high'}, 'confidence': 0.95, 'source': 'chat', 'updated_at': '2026-04-02T10:00:00+05:30'},
    'pending_followups': {'key': 'pending_followups', 'value': {'items': [{'who': 'Rahul', 'topic': 'investment terms', 'due': '2026-04-05'}, {'who': 'design team', 'topic': 'logo sign-off'}]}, 'confidence': 0.9, 'source': 'chat', 'updated_at': '2026-04-02T10:00:00+05:30'},
    'user_preferences': {'key': 'user_preferences', 'value': {'briefing_style': 'concise with detail', 'communication': 'direct and brief'}, 'confidence': 0.9, 'source': 'explicit', 'updated_at': '2026-04-01T10:00:00+05:30'},
}

_task_store = [
    {'id': 1, 'title': 'Follow up with Rahul on investment terms', 'description': '15% equity for ₹50L — 4 days overdue', 'status': 'pending', 'priority': 'urgent', 'deadline': '2026-04-05T18:00:00+05:30', 'project_id': 1},
    {'id': 2, 'title': 'Submit GCP Hackathon project', 'description': 'Deploy Cortex, create demo video and slides', 'status': 'pending', 'priority': 'high', 'deadline': '2026-04-08T23:59:00+05:30', 'project_id': 2},
    {'id': 3, 'title': 'Review Bhooyam logo design', 'description': 'Design team sent mockups, need sign-off', 'status': 'pending', 'priority': 'high', 'deadline': '2026-04-07T17:00:00+05:30', 'project_id': 1},
    {'id': 4, 'title': 'Test hydroponic prototype', 'description': 'Run nutrient flow test on Jal prototype', 'status': 'pending', 'priority': 'medium', 'deadline': '2026-04-10T10:00:00+05:30', 'project_id': 1},
    {'id': 5, 'title': 'Write freelance proposal for client X', 'description': 'Website automation project — $500 estimate', 'status': 'pending', 'priority': 'medium', 'deadline': '2026-04-06T12:00:00+05:30', 'project_id': None},
    {'id': 6, 'title': 'Complete hackathon codelabs Track 2', 'description': 'MCP tools codelab — Travel Assistant', 'status': 'in_progress', 'priority': 'medium', 'deadline': '2026-04-06T20:00:00+05:30', 'project_id': 2},
    {'id': 7, 'title': 'Update MEMORY.md with hackathon progress', 'description': 'Document Track 1 submission', 'status': 'done', 'priority': 'low', 'deadline': '2026-04-02T22:00:00+05:30', 'project_id': None},
]

_cal_events = [
    {'id': 'evt1', 'summary': 'Design Review', 'start': '2026-04-05T11:00:00+05:30', 'end': '2026-04-05T12:00:00+05:30', 'is_all_day': False, 'location': 'Google Meet', 'attendees': ['design@team.com'], 'description': 'Jal app UX flow review'},
    {'id': 'evt2', 'summary': 'Rahul: Investment Follow-up', 'start': '2026-04-05T14:00:00+05:30', 'end': '2026-04-05T14:30:00+05:30', 'is_all_day': False, 'location': 'Zoom', 'attendees': ['rahul@email.com'], 'description': '15% equity for ₹50L discussion'},
]

_session_store = {}  # session_id -> messages
_email_drafts = []  # pending drafts awaiting approval

# ============================================================================
# WEB PAGES
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/memory')
def memory_page():
    return render_template('memory.html')

@app.route('/tasks')
def tasks_page():
    return render_template('tasks.html')

# ============================================================================
# REST API
# ============================================================================

@app.route('/api/query', methods=['POST'])
def api_query():
    """
    Main Cortex query endpoint.
    Returns a pre-composed response for the demo scenario.
    """
    data = request.get_json() or {}
    user_message = data.get('message', '').lower()
    session_id = data.get('session_id', 'demo-session')
    
    # Initialize session
    if session_id not in _session_store:
        _session_store[session_id] = []
    _session_store[session_id].append({'role': 'user', 'message': user_message})
    
    # Demo response logic
    if 'plate' in user_message or 'today' in user_message or 'morning' in user_message or 'briefing' in user_message:
        response = MORNING_BRIEFING
    elif 'follow up' in user_message or 'rahul' in user_message or 'send email' in user_message:
        response = RAHUL_EMAIL_RESPONSE
    elif 'memory' in user_message and ('show' in user_message or 'what' in user_message):
        response = MEMORY_CHECK
    elif 'task' in user_message and ('show' in user_message or 'list' in user_message):
        response = TASKS_RESPONSE
    else:
        response = f"Cortex received: '{user_message}'. I'm running in demo mode with in-memory storage. Configure a real database for full functionality. Try asking: 'What's on my plate today?' or 'Follow up with Rahul'"
    
    _session_store[session_id].append({'role': 'cortex', 'message': response})
    
    return jsonify({
        'response': response,
        'session_id': session_id,
        'agent': 'cortex',
        'mode': 'demo' if DEMO_MODE else 'production',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/memory', methods=['GET'])
def api_memory_list():
    return jsonify({'memory': list(_memory_store.values())})

@app.route('/api/memory', methods=['POST'])
def api_memory_put():
    data = request.get_json()
    key = data.get('key')
    if key:
        _memory_store[key] = {'key': key, 'value': data.get('value', {}), 'confidence': data.get('confidence', 0.9), 'source': data.get('source', 'api'), 'updated_at': datetime.now().isoformat()}
    return jsonify({'result': _memory_store.get(key, {})})

@app.route('/api/memory/<key>', methods=['GET'])
def api_memory_get(key):
    entry = _memory_store.get(key)
    if entry:
        return jsonify(entry)
    return jsonify({'error': f"Key '{key}' not found"}), 404

@app.route('/api/tasks', methods=['GET'])
def api_tasks_list():
    status = request.args.get('status')
    priority = request.args.get('priority')
    tasks = _task_store
    if status:
        tasks = [t for t in tasks if t['status'] == status]
    if priority:
        tasks = [t for t in tasks if t['priority'] == priority]
    return jsonify({'tasks': tasks})

@app.route('/api/tasks', methods=['POST'])
def api_tasks_create():
    data = request.get_json()
    new_id = max(t['id'] for t in _task_store) + 1
    task = {'id': new_id, 'title': data.get('title', ''), 'description': data.get('description', ''), 'status': 'pending', 'priority': data.get('priority', 'medium'), 'deadline': data.get('deadline'), 'project_id': data.get('project_id')}
    _task_store.append(task)
    return jsonify({'task': task}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
def api_tasks_update(task_id):
    for task in _task_store:
        if task['id'] == task_id:
            data = request.get_json() or {}
            for k in ['status', 'title', 'description', 'priority']:
                if k in data:
                    task[k] = data[k]
            return jsonify({'task': task})
    return jsonify({'error': f'Task {task_id} not found'}), 404

@app.route('/api/calendar/today', methods=['GET'])
def api_calendar_today():
    return jsonify({'events': _cal_events, 'date': datetime.now().strftime('%Y-%m-%d')})

@app.route('/api/email/search', methods=['GET'])
def api_email_search():
    return jsonify({'results': [{'id': 'em1', 'from': 'Rahul Sharma <rahul@email.com>', 'subject': 'Re: Investment Terms Discussion', 'date': '2026-04-03', 'snippet': 'Hi Aayush, following up on our conversation about the 15% equity proposal...'}]})

@app.route('/api/email/draft', methods=['POST'])
def api_email_draft():
    data = request.get_json()
    draft = {'draft_id': str(uuid.uuid4()), 'to': data.get('to', ''), 'subject': data.get('subject', ''), 'status': 'Draft created - awaiting approval'}
    _email_drafts.append(draft)
    return jsonify({'draft': draft})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'agent': 'cortex', 'mode': 'demo' if DEMO_MODE else 'production', 'timestamp': datetime.now().isoformat()})

# ============================================================================
# DEMO RESPONSE TEMPLATES
# ============================================================================

MORNING_BRIEFING = """Good morning! Here's your briefing for April 5, 2026:

📅 TODAY'S SCHEDULE:
• 11:00 AM — Design Review (1hr) 📍 Google Meet
  Last discussed: Jal app UX flow — decisions needed on navigation hierarchy
• 2:00 PM — Rahul: Investment Follow-up (30min) 📍 Zoom
  🔴 OVERDUE: 15% equity for ₹50L. Rahul was supposed to revert in 3 days — that's 4 days ago now.

📋 PENDING TASKS:
🔴 URGENT: Follow up with Rahul — by TODAY (Apr 5)
🟠 HIGH: Submit GCP Hackathon Project — by Apr 8
🟠 HIGH: Review Bhooyam Logo — by Apr 7
🟡 MEDIUM: Test hydroponic prototype — by Apr 10

📧 ACTION ITEMS FROM EMAIL:
• Rahul sent email Apr 3 (unread) — "following up on equity terms"
• Invoice approval needed before 5pm today

🧠 FROM YOUR MEMORY:
• Q1 goal: Launch Ankuran Jal MVP by April 15
• You committed to: "close Rahul investment this week"
• Working on: GCP Gen AI Hackathon (submit by April 8)

What would you like to focus on first?"""

RAHUL_EMAIL_RESPONSE = """I found Rahul's context in your memory and email. Here's the draft:

✏️ DRAFT EMAIL — Review before sending:

To: rahul@email.com
Subject: Re: Investment Terms Discussion

Hi Rahul,

Following up from our conversation about the 15% equity proposal for ₹50L.

You mentioned you'd revert within 3 days — it's been 4 days now. Is there an update on the legal review?

Let me know if you need anything from our side to move this forward.

Best, Aayush

---
Reply "send", "yes", or "go ahead" to send this email.
Reply "edit" to modify the draft."""

MEMORY_CHECK = """Here's what's stored in your memory model:

🧠 Memory Entries (5):

rahul_context (95% confidence, source: chat)
{'name': 'Rahul Sharma', 'topic': '15% equity for ₹50L', 'status': 'waiting_on_rahul', 'notes': '4 days overdue'}

current_project (95% confidence, source: chat)
{'name': 'Bhooyam Ankuran Jal', 'stage': 'pre-launch', 'priority': 'high'}

pending_followups (90% confidence, source: chat)
{'items': [{'who': 'Rahul', 'topic': 'investment terms'}, {'who': 'design team', 'topic': 'logo sign-off'}]}

user_preferences (90% confidence, source: explicit)
{'briefing_style': 'concise with detail', 'communication': 'direct and brief'}

q1_goals (90% confidence, source: chat)
{'goals': ['Launch Ankuran Jal MVP', 'Close Rahul investment', 'Complete GCP hackathon']}"""

TASKS_RESPONSE = """📋 Your Tasks (6):

🔴 URGENT:
• Follow up with Rahul on investment terms — by Apr 5 (TODAY) — #1

🟠 HIGH:
• Submit GCP Hackathon project — by Apr 8 — #2
• Review Bhooyam logo design — by Apr 7 — #3

🟡 MEDIUM:
• Test hydroponic prototype — by Apr 10 — #4
• Write freelance proposal — by Apr 6 — #5

⚪ LOW / DONE:
• Update MEMORY.md — COMPLETED — #7"""

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
    print(f"Starting Cortex in {'DEMO' if DEMO_MODE else 'PRODUCTION'} mode on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
