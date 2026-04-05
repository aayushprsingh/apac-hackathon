# Cortex — Persistent Multi-Agent Productivity Assistant

> A production-aware AI system that remembers who you are, pulls your emails and calendar automatically, and helps you manage tasks — without you lifting a finger.

**Built for Google Cloud Gen AI Academy APAC 2026 | Cohort 1 Hackathon**

---

## What It Does

Cortex is different from every other AI assistant because it's **persistent**. While ChatGPT and Claude forget everything after each conversation, Cortex builds a living model of you — your projects, your people, your commitments — and uses that context to actually manage your work.

**The moment it clicks:**

> You open Cortex, and before you even ask anything, it says:
> *"Good morning. You have 3 meetings today, 2 emails need attention from last week, and you promised Rahul a follow-up on the investment terms — that's 4 days overdue."*

That's not a chat response. That's a chief of staff who actually knows you.

---

## Live Demo

**🌐 [https://cortex-agent-455006885273.asia-south1.run.app](https://cortex-agent-455006885273.asia-south1.run.app)**

Click **"Try as Guest"** — no account needed. Or connect your Google account for automatic email and calendar pull.

---

## Key Features

### 🧠 Persistent Memory Model
Every conversation updates Cortex's memory of you. It stores facts, preferences, relationships, and commitments — and surfaces them at exactly the right moment. Not just today's data. Everything you've ever told it.

### 🤖 Multi-Agent Architecture
One message triggers multiple specialized agents working in parallel:
- **Cortex Coordinator** — understands intent, orchestrates everything
- **Memory Agent** — retrieves and stores your personal context
- **Task Agent** — manages your task list with priorities and deadlines
- **Scheduler Agent** — reads your calendar, checks availability
- **Email Agent** — searches your inbox, drafts responses

### ✅ Checkpoint Workflows
Before any external action — sending an email, creating a calendar event — Cortex shows you exactly what it's about to do and waits for your approval. You stay in control.

### 📊 Automatic Data Pull (Google Sign-In)
When you sign in with Google, Cortex automatically:
- Pulls your calendar events for the next 7 days
- Imports recent emails from your inbox
- Scans emails for task-like content (deadlines, follow-ups, commitments)
- Assembles everything into your morning briefing — before you ask

### 📱 Multi-User, Per-User Data Isolation
Every user has their own completely separate memory, tasks, calendar, and email data. Your data is yours. No cross-contamination.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│         CORTEX COORDINATOR              │
│     Root LlmAgent (Gemini 2.5 Flash)   │
│  • Understands natural language         │
│  • Orchestrates sub-agents              │
│  • Enforces checkpoint pattern           │
│  • Synthesizes responses                │
└───────────────┬─────────────────────────┘
        ┌───────┼───────┬─────────┐
        ▼       ▼       ▼         ▼
  ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐
  │Memory  │ │Task  │ │Sched-  │ │ Email  │
  │Agent   │ │Agent │ │uler    │ │ Agent  │
  │        │ │      │ │Agent   │ │        │
  └────┬───┘ └──┬───┘ └───┬────┘ └───┬────┘
       │        │          │          │
       └────────┴─────┬────┴──────────┘
                       ▼
           ┌──────────────────────┐
           │   DATA LAYER         │
           │ Firebase Firestore   │
           │ (per-user isolated)  │
           │ Gmail + Calendar API │
           └──────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Google ADK (Agent Development Kit) |
| LLM | Gemini 2.5 Flash |
| Auth | Firebase Auth (Google OAuth + Email/Password) |
| Database | Firebase Firestore (per-user, auto-synced) |
| Calendar | Google Calendar API (auto-pull on sign-in) |
| Email | Gmail API (auto-pull on sign-in) |
| Web | Flask + Vanilla JS (no framework, fast) |
| Deployment | Google Cloud Run (serverless, auto-scaling) |

---

## Quick Start

### Try the Live Demo

1. Visit [https://cortex-agent-455006885273.asia-south1.run.app](https://cortex-agent-455006885273.asia-south1.run.app)
2. Click **"Try as Guest"**
3. Ask: "What's on my plate today?"

### Run Locally

```bash
# Clone
git clone https://github.com/aayushprsingh/apac-hackathon.git
cd apac-hackathon

# Install
pip install -r requirements.txt

# Run
cd app
python app.py
# Visit http://localhost:8080
```

### Deploy to Cloud Run

```bash
gcloud builds submit --tag asia-south1-docker.pkg.dev/YOUR_PROJECT/cortex-repo/cortex-agent:v1 .
gcloud run deploy cortex-agent \
  --image=asia-south1-docker.pkg.dev/YOUR_PROJECT/cortex-repo/cortex-agent:v1 \
  --platform=managed --region=asia-south1 --allow-unauthenticated
```

---

## Project Structure

```
apac-hackathon/
├── app/
│   ├── app.py              # Flask app + all API routes
│   ├── firebase_auth.py     # Firebase Admin + Gmail/Calendar auto-pull
│   ├── __init__.py
│   ├── requirements.txt
│   └── templates/
│       ├── login.html       # Auth page (Google OAuth + Guest)
│       ├── onboarding.html  # 3-step profile setup
│       └── dashboard.html   # Main app (chat + memory + tasks)
├── agents/                  # ADK agent definitions
├── tools/                  # Gmail, Calendar, DB tool wrappers
├── db/                     # PostgreSQL schema (production)
├── demo/
│   ├── demo_script.md      # Full demo walkthrough
│   ├── RECORD_DEMO.md      # Video recording guide
│   └── Cortex_Presentation.pdf
├── FIREBASE_SETUP.md       # Firebase + Gmail/Calendar setup guide
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Submission

| Item | Link |
|------|------|
| Live Demo | https://cortex-agent-455006885273.asia-south1.run.app |
| GitHub | https://github.com/aayushprsingh/apac-hackathon |
| Hackathon | https://vision.hack2skill.com/event/apac-genaiacademy |

---

## Why This Fits the Problem Statement

> "Build a multi-agent AI system that helps users manage tasks, schedules, and information by interacting with multiple tools and data sources."

| Requirement | How We Meet It |
|-------------|----------------|
| Primary root agent + sub-agents | ✅ Cortex Coordinator + 4 sub-agents (Memory, Task, Scheduler, Email) |
| Store/retrieve structured data | ✅ Firebase Firestore with per-user isolation |
| Interact with multiple tools | ✅ Gmail API, Google Calendar API, Firestore |
| Multi-step workflows | ✅ Coordinator → sub-agent → checkpoint → execute |
| API-based system | ✅ REST API on Cloud Run |
| Automatic data pull | ✅ Gmail + Calendar pulled on Google Sign-In |
| Zero manual data entry | ✅ Sign in with Google → everything auto-imports |

---

## Limitations & Future Work

- **Demo mode** (current): Pre-seeded data, Gmail/Calendar pull requires Firebase setup
- **Production**: Full Firebase + Gmail/Calendar auto-pull activates once OAuth is configured
- **Mobile**: Web UI works on mobile, native apps are future work

---

## Author

**Aayush Pratap Singh**  
Founder, Bhooyam Agritech Pvt. Ltd.  
[LinkedIn](https://linkedin.com/in/aayushprsingh) | [GitHub](https://github.com/aayushprsingh)

---

*Built with Google ADK + Gemini 2.5 Flash + Firebase + Cloud Run*
