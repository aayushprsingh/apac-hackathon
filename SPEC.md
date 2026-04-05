# Cortex — Cohort Hackathon Project SPEC
## Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

---

## 1. Concept & One-Line Pitch

**Cortex** is a persistent multi-agent productivity assistant that remembers your work across sessions, proactively prepares your context, and coordinates specialized sub-agents to execute multi-step tasks end-to-end.

> "Your AI that actually knows you between conversations."

---

## 2. Alignment with Problem Statement

| Requirement | Implementation |
|---|---|
| Primary root agent + sub-agents | Cortex Coordinator → Memory/Task/Scheduler/Email sub-agents |
| Store/retrieve structured data | PostgreSQL (Cloud SQL) — user_model, tasks, projects, sessions, action_log |
| MCP tools (calendar, task, notes) | Gmail API + Google Calendar API (via google-api-python-client) |
| Multi-step workflows | SequentialAgent pattern with human-in-the-loop checkpoints |
| API-based system | ADK on Cloud Run as REST API |

✅ **Fits all requirements.**

---

## 3. Architecture

```
User → Cortex Coordinator (LlmAgent)
            ↓ coordinates
    ┌────────┼────────┐
    ↓        ↓        ↓
Memory   Scheduler   Email
Agent    Agent      Agent
    ↓        ↓        ↓
PostgreSQL  Gmail API  Calendar API
(Cloud SQL)
```

**5 Agents:**
- **Cortex Coordinator** — root agent, orchestration, user interaction
- **Memory Agent** — persistent user model in PostgreSQL
- **Task Agent** — task CRUD in PostgreSQL
- **Scheduler Agent** — Google Calendar reads via API
- **Email Agent** — Gmail reads/drafts via API

---

## 4. Database Schema (PostgreSQL)

```sql
-- User's persistent memory model
CREATE TABLE user_model (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(50) DEFAULT 'chat',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(10) DEFAULT 'medium',
    deadline TIMESTAMP,
    project_id INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Projects
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    context JSONB,
    last_interaction TIMESTAMP DEFAULT NOW()
);

-- Action log
CREATE TABLE action_log (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    agent VARCHAR(50),
    action VARCHAR(100),
    payload JSONB,
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. MCP / Tool Integration

Since official Gmail/Calendar MCP servers require complex OAuth Desktop flows, we use the REST APIs directly — more reliable for hackathon timeline:

**Gmail API (via google-api-python-client):**
- `search_emails(query, max_results=5)` — search inbox
- `read_email(thread_id)` — get full email
- `draft_email(to, subject, body)` — create draft

**Google Calendar API:**
- `list_events(day, max_results=10)` — get day's events
- `get_event(event_id)` — event details
- `create_event(title, start_time, end_time, attendees)` — add to calendar

**PostgreSQL (via psycopg2):**
- `memory_get(key)` — retrieve from user_model
- `memory_put(key, value, confidence, source)` — store fact
- `tasks_crud(operation, ...)` — create/read/update/list tasks

---

## 6. Project Structure

```
apac-hackathon/
├── SPEC.md
├── README.md
├── requirements.txt
├── .env.example
├── root_agent.yaml          ← ADK root agent config
├── agents/
│   ├── __init__.py
│   ├── cortex.py            ← Root coordinator agent
│   ├── memory.py            ← Memory (PostgreSQL) agent
│   ├── task.py              ← Task CRUD agent
│   ├── scheduler.py         ← Calendar agent
│   └── email.py             ← Email agent
├── tools/
│   ├── __init__.py
│   ├── gmail_tools.py       ← Gmail API tools
│   ├── calendar_tools.py    ← Calendar API tools
│   └── db_tools.py          ← PostgreSQL tools
├── db/
│   ├── schema.sql           ← Database schema
│   └── seed.sql             ← Sample data for demo
├── app/
│   ├── app.py               ← Flask web app (web UI + API)
│   └── requirements.txt
├── deploy.sh / deploy.ps1   ← Cloud Run deployment
└── demo/
    └── demo_script.md       ← Demo walkthrough script
```

---

## 7. MVP Scope (3-Day Hackathon)

### Must Have (Submit-Ready)
1. ✅ Cortex Coordinator with all 4 sub-agents wired
2. ✅ Memory Agent → PostgreSQL (user_model table working)
3. ✅ Task Agent → PostgreSQL (tasks table CRUD)
4. ✅ Scheduler Agent → Google Calendar API (list events, create event)
5. ✅ Email Agent → Gmail API (search, draft)
6. ✅ Multi-step workflow with checkpoint (draft email → user approve → confirm)
7. ✅ Flask web app as UI
8. ✅ Cloud Run deployment
9. ✅ GitHub repo
10. ✅ PDF slides (2-3 slides)
11. ✅ Demo video (YouTube/unlisted)

### Demo Scenario
**"Good morning briefing" → "Follow up with Rahul" workflow**

1. User: "What's on my plate today?"
   → Cortex checks Calendar + Memory + Emails → assembles briefing
   
2. User: "Send a follow-up to Rahul about our last discussion"
   → Cortex: Memory Agent (get Rahul context) → Email Agent (draft) → show draft → user approves → sent → memory updated

---

## 8. GCP Resources Needed

- **Cloud SQL PostgreSQL** (or AlloyDB) — free tier: 30 days
- **Cloud Run** — ADK web server
- **Service Account** — with Cloud SQL Client + Vertex AI roles
- **APIs enabled:** gmail.googleapis.com, calendar-json.googleapis.com, run.googleapis.com, sqladmin.googleapis.com

---

## 9. Submission Checklist

- [ ] Cloud Run URL submitted
- [ ] GitHub repo URL submitted
- [ ] PDF presentation (2-3 slides) submitted
- [ ] Demo video link submitted

---

## 10. Timeline (3 Days)

| Day | Focus |
|-----|-------|
| Day 1 | Scaffold + DB + Memory Agent + Task Agent |
| Day 2 | Scheduler + Email Agent + Coordinator wiring |
| Day 3 | Deploy + Demo video + PDF slides + Submit |

---

_Last updated: 2026-04-05_
