# Cortex Demo Recording Guide

**Time needed:** 5-7 minutes
**Tools:** OBS Studio (already installed) + Chrome

---

## Setup

1. Open OBS Studio → Settings → Output → Recording Quality: "High Quality" → Format: MP4
2. Create a new Scene named "Cortex Demo"
3. Add a Window Capture for Chrome
4. Hit **Start Recording**

---

## Scene 1: Opening (0:00 – 0:30)

Open Chrome to the live demo URL. Show the login page briefly.

**Say:** "This is Cortex — a persistent multi-agent productivity assistant. Every AI tool you've used forgets everything after each conversation. Cortex remembers."

---

## Scene 2: Morning Briefing (0:30 – 2:00)

In the chat, type: `What's on my plate today?`

**What to highlight when the response appears:**

- "Shows my calendar AND tasks in one shot — no separate apps to check"
- "It knows I have a system design review with Alex today — that's from memory, not today's data"
- "Jordan Lee is waiting on me — this was stored from our previous conversation"

Open the Memory page in a new tab: `/memory`

**Say:** "This is the persistent memory model. The fact that Jordan is waiting on me was stored from a previous conversation. Cortex learns and remembers across sessions."

---

## Scene 3: Task Management (2:00 – 3:00)

Click the Tasks link in the sidebar. Show the priority filters.

**Say:** "Tasks are automatically prioritized by urgency. Notice the tasks from the morning briefing are here — the system design review, the roadmap follow-up. Everything is connected."

Click "High" filter to show only high-priority tasks.

---

## Scene 4: API Demo (3:00 – 4:00)

Open a new terminal window. Run the health check and a query.

```bash
curl https://cortex-agent-455006885273.asia-south1.run.app/api/health

curl -X POST https://cortex-agent-455006885273.asia-south1.run.app/api/query \
  -H "Content-Type: application/json" \
  -d '{"message":"What is on my plate today?"}'
```

**Say:** "It's also a REST API. Every capability is accessible programmatically — so you can integrate it into your own tools and workflows."

---

## Scene 5: Architecture Overview (4:00 – 5:30)

Show the GitHub repo and briefly walk through the structure.

**Say:** "Built with Google ADK — five agents in total. The Coordinator orchestrates specialized sub-agents, each handling one domain: Memory, Tasks, Calendar, and Email. All data is stored per-user in Firebase Firestore, completely isolated."

Show the agent files in the repo:
- `agents/cortex.py` — Root coordinator
- `agents/memory.py`, `task.py`, `scheduler.py`, `email.py` — Sub-agents
- `app/app.py` — Flask REST API
- `app/firebase_auth.py` — Firebase + Gmail/Calendar auto-pull

---

## Scene 6: Submission Summary (5:30 – 6:00)

Show the deployed URL and GitHub repo on screen.

```
https://cortex-agent-455006885273.asia-south1.run.app
https://github.com/aayushprsingh/apac-hackathon
```

**Say:** "Deployed on Google Cloud Run. Sign in with Google to connect your real email and calendar — and Cortex pulls everything automatically, zero manual setup needed. Thank you."

---

## Stop Recording

OBS → Stop Recording. Upload to YouTube (unlisted).

---

## Quick Links for Demo

| What | URL |
|------|-----|
| Main app | https://cortex-agent-455006885273.asia-south1.run.app |
| Memory page | https://cortex-agent-455006885273.asia-south1.run.app/memory |
| Tasks page | https://cortex-agent-455006885273.asia-south1.run.app/tasks |
| GitHub | https://github.com/aayushprsingh/apac-hackathon |
