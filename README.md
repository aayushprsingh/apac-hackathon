# Cortex — Personal Productivity Assistant

> A persistent multi-agent AI system that remembers your work across sessions, proactively prepares your context, and coordinates specialized sub-agents to handle tasks end-to-end.
> Built for **Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon**.

[![Cohort 1](https://img.shields.io/badge/Cohort-1-4285F4?style=flat-square)](https://vision.hack2skill.com/event/apac-genaiacademy)
[![ADK](https://img.shields.io/badge/Framework-Google%20ADK-4285F4?style=flat-square)](https://cloud.google.com/vertex-ai/generative-ai/docs/model-as-tool/agent-define)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 🎯 What It Does

**The "wow" moment:** Unlike every other AI tool that forgets everything after each conversation, Cortex builds a persistent memory model — it knows your projects, relationships, and commitments across sessions.

**Example interaction:**
> **You:** "What's on my plate today?"  
> **Cortex:** *(checks your calendar + memory + emails)*  
> "Good morning! You have 2 meetings today. For your 2pm with Rahul — you're waiting on him for the investment terms (15% equity, ₹50L). His reply is 4 days overdue. You also have 1 urgent task: submit your hackathon project by April 8."

> **You:** "Send a follow-up to Rahul"  
> **Cortex:** *(drafts email using memory context, shows draft for your approval)*  
> "Does this look right? Reply 'send' to go ahead."

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌──────────────────────────────────────────┐
│  Cortex Coordinator (Root LlmAgent)     │
│  • Understands intent                    │
│  • Orchestrates sub-agents              │
│  • Synthesizes responses                │
│  • Enforces checkpoint workflow         │
└───────────────┬──────────────────────────┘
                │
    ┌───────────┼───────────┬────────────┐
    ▼           ▼           ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│ Memory  │ │  Task   │ │Scheduler│ │  Email   │
│ Agent   │ │ Agent   │ │ Agent   │ │  Agent   │
│(Postgre)│ │(Postgre)│ │Calendar │ │  Gmail   │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     └───────────┴─────┬─────┴───────────┘
                       ▼
              PostgreSQL (Cloud SQL)
              user_model · tasks · projects
```

**5 Agents, 3 Data Sources:**
- **Cortex Coordinator** — orchestrates everything
- **Memory Agent** — PostgreSQL user model (what you know about the user)
- **Task Agent** — PostgreSQL task management
- **Scheduler Agent** — Google Calendar API
- **Email Agent** — Gmail API

---

## 📁 Project Structure

```
apac-hackathon/
├── SPEC.md              ← This file
├── README.md            ← Documentation
├── requirements.txt     ← Python dependencies
├── .env.example         ← Environment template
├── root_agent.yaml      ← ADK agent config
│
├── agents/
│   ├── cortex.py        ← Root coordinator agent
│   ├── memory.py        ← Memory (user model) agent
│   ├── task.py          ← Task CRUD agent
│   ├── scheduler.py     ← Calendar agent
│   └── email.py         ← Email agent
│
├── tools/
│   ├── db_tools.py      ← PostgreSQL tools (memory, tasks)
│   ├── gmail_tools.py   ← Gmail API tools
│   └── calendar_tools.py ← Google Calendar tools
│
├── db/
│   ├── schema.sql       ← Database schema
│   └── seed.sql         ← Sample data for demo
│
├── app/
│   ├── app.py           ← Flask web app
│   ├── requirements.txt
│   └── templates/       ← Web UI (index, memory, tasks)
│
└── deploy.sh / deploy.ps1 ← Cloud Run deployment
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Fill in your values in .env
```

### 3. Set Up Database

Create a PostgreSQL database (local or Cloud SQL) and run:

```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f db/schema.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f db/seed.sql
```

### 4. Configure Google OAuth (for Gmail/Calendar)

1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download as `credentials.json`
4. Run: `python tools/authenticate.py --gmail --calendar`

### 5. Test Locally

```bash
cd app
python app.py
# Visit http://localhost:8080
```

---

## 🚀 Deployment

### Prerequisites
- Google Cloud project with billing enabled
- Cloud SQL PostgreSQL instance created
- APIs enabled: `run.googleapis.com`, `calendar-json.googleapis.com`, `gmail.googleapis.com`

### Deploy to Cloud Run

**Bash (Linux/Mac/Cloud Shell):**
```bash
./deploy.sh
```

**PowerShell (Windows):**
```powershell
.\deploy.ps1
```

---

## 🔑 Key Features

### 1. Persistent Memory
Every interaction updates the user model. Ask Cortex about something you discussed days ago — it remembers.

### 2. Multi-Agent Coordination
One user message triggers multiple specialized agents working together. The coordinator orchestrates, synthesizes, and responds.

### 3. Checkpoint Workflows
For sensitive actions (sending emails), Cortex ALWAYS shows the draft first and waits for explicit approval.

### 4. Proactive Context Assembly
"Give me a briefing" triggers calendar + memory + email simultaneously — assembled into one coherent briefing.

### 5. API-First Design
Every capability is accessible via REST API. The web UI is optional.

---

## 📋 Submission Checklist

- [ ] Cloud Run URL deployed
- [ ] GitHub repository linked
- [ ] PDF presentation (2-3 slides)
- [ ] Demo video (YouTube/unlisted)

---

## 🤖 Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Google ADK (Agent Development Kit) |
| LLM | Gemini 2.5 Flash |
| Database | PostgreSQL (Cloud SQL) |
| Calendar | Google Calendar API |
| Email | Gmail API |
| Web | Flask |
| Deployment | Google Cloud Run |

---

## 👤 Author

**Aayush Pratap Singh**  
Bhooyam Agritech Private Limited  
[GitHub](https://github.com/aayushprsingh) | [LinkedIn](https://linkedin.com/in/aayushprsingh)

---

Built for **Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon**
