# Cohort 1 Hackathon — Submission Checklist
## Google Cloud Gen AI Academy APAC 2026

---

## LIVE DEPLOYMENT

**🌐 Cloud Run URL:** https://cortex-agent-455006885273.asia-south1.run.app

**API Endpoints:**
- `GET /api/health` — Health check
- `POST /api/query` — Main Cortex query endpoint (try: "What's on my plate today?")
- `GET /api/memory` — List all memory entries
- `GET /api/tasks` — List all tasks
- `GET /api/calendar/today` — Today's calendar events
- `GET /api/email/search?q=rahul` — Search emails

---

## SUBMISSION FORM — What to Fill In

| Field | Value |
|-------|-------|
| **Project Name** | Cortex |
| **Description** | Persistent multi-agent productivity assistant with memory across sessions |
| **Track** | Cohort 1 Hackathon |
| **Team Size** | Individual |
| **Cloud Run URL** | https://cortex-agent-455006885273.asia-south1.run.app |
| **GitHub Repository** | https://github.com/aayushprsingh/apac-hackathon |
| **Demo Video URL** | [YouTube unlisted link after recording] |
| **PDF Presentation** | Upload: `demo/Cortex_Presentation.pdf` |

---

## SUBMISSION URL
**👉 https://vision.hack2skill.com/event/apac-genaiacademy**

---

## HOW TO RECORD DEMO VIDEO (5-7 minutes)

1. Open OBS Studio → Start Recording
2. Follow `demo/RECORD_DEMO.md` for exact scenes and narration
3. Stop recording → Export as MP4
4. Upload to YouTube (unlisted) or Google Drive
5. Paste link in submission form

**Quick demo (3 key scenes):**
1. Web UI: "What's on my plate today?" → full briefing response
2. Memory page: Show `rahul_context` with overdue investment details
3. API curl: Show REST endpoint returning JSON

---

## REQUIREMENT MAPPING

| Requirement | How Met |
|-------------|---------|
| Primary root agent + sub-agents | ✅ Cortex Coordinator + 4 sub-agents (Memory, Task, Scheduler, Email) |
| Store/retrieve structured data | ✅ PostgreSQL schema + in-memory demo storage |
| MCP tools integration | ✅ Gmail API + Google Calendar API (REST) |
| Multi-step workflows | ✅ Draft-then-confirm email pattern |
| REST API on Cloud Run | ✅ https://cortex-agent-455006885273.asia-south1.run.app |
| Cloud Run URL | ✅ Submitted |
| GitHub repo | ✅ github.com/aayushprsingh/apac-hackathon |
| PDF slides (2-3) | ✅ demo/Cortex_Presentation.pdf |
| Demo video | ⏳ Record and upload |

---

## FILES IN SUBMISSION

```
apac-hackathon/
├── README.md              ← Main documentation
├── SUBMISSION.md         ← This file
├── SPEC.md               ← Technical specification
├── agents/               ← 5 ADK agents (coordinator + 4 sub-agents)
├── tools/                ← db_tools, gmail_tools, calendar_tools
├── db/schema.sql         ← PostgreSQL schema
├── app/app.py            ← Flask REST API + web UI
├── demo/
│   ├── demo_script.md    ← Full demo walkthrough
│   ├── RECORD_DEMO.md    ← Video recording guide
│   └── Cortex_Presentation.pdf ← 3-slide PDF
├── Dockerfile            ← Cloud Run container
├── deploy.sh / .ps1      ← Deployment scripts
└── requirements.txt     ← Dependencies
```

---

## KEY DEMONSTRATION POINTS

1. **Persistent Memory** — "Rahul context" stored from previous session, surfaced in today's briefing
2. **Multi-Agent Coordination** — One message → queries Calendar + Memory + Tasks + Email simultaneously
3. **Checkpoint Workflow** — Email draft shown for review BEFORE sending (responsible AI)
4. **REST API** — Every capability accessible via HTTP
5. **Production Deployment** — Running on Cloud Run, not localhost

---

## DEADLINE

**April 8, 2026, 11:59 PM (your timezone)**

Reminder set for April 8, 9:00 AM IST via WhatsApp.

**Do not miss this.**
