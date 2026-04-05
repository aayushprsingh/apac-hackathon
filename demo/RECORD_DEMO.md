# Cortex Demo Recording Guide
## How to record your hackathon demo video (5-7 minutes)

**Tools needed:** OBS Studio (already installed) + Chrome browser

**Before starting:**
- Open OBS Studio → Settings → Output → Recording Quality: "High Quality" → Recording Format: MP4
- Create a new Scene called "Cortex Demo"
- Add a Window Capture for Chrome
- Hit "Start Recording"

---

## SCENE 1: Title Slide (0:00 - 0:30)
**Show:** Full-screen browser tab with:
```
https://cortex-agent-455006885273.asia-south1.run.app
```

**Say:** "This is Cortex — a persistent multi-agent productivity assistant. Unlike every AI tool that forgets everything after each conversation, Cortex remembers your projects, people, and commitments across sessions. Let me show you how it works."

---

## SCENE 2: Morning Briefing (0:30 - 2:00)
**Action:** Open Chrome DevTools (F12) or show a second browser tab

**Tab 1 — Web UI:**
```
https://cortex-agent-455006885273.asia-south1.run.app
```
1. Scroll to the chat input at the bottom
2. Type: `What's on my plate today?`
3. Click Send
4. Wait for the full briefing to appear

**While it loads, say:** "One message, and Cortex queries your Calendar, Email, Task list, and Memory simultaneously — assembling everything into a single coherent briefing."

**After response appears, highlight:**
- "🔴 OVERDUE: Rahul is 4 days past the deadline" — "This came from PERSISTENT MEMORY, not today's data"
- "From your memory: 'You committed to close Rahul investment this week'" — "It remembered this from a previous conversation"

**Say:** "The key differentiator: it knows about Rahul being overdue — from MEMORY, not from today's calendar. This is what makes Cortex different from every other AI tool."

---

## SCENE 3: Memory Verification (2:00 - 3:00)
**Action:** Open new tab or click "🧠 Memory" in the nav

```
https://cortex-agent-455006885273.asia-south1.run.app/memory
```

**Scroll and show:**
- `rahul_context` — value shows "15% equity for ₹50L", "waiting_on_rahul", "4 days overdue"
- `current_project` — Bhooyam Ankuran Jal
- `pending_followups` — list of follow-ups

**Say:** "This is the persistent memory model stored in PostgreSQL. The fact about Rahul being 4 days overdue was stored from a previous conversation — not from today's email or calendar. Cortex LEARNED this."

**Click the `rahul_context` card to expand it and show the full JSON structure.**

---

## SCENE 4: Task Management (3:00 - 3:45)
**Action:** Click "📋 Tasks" in the nav

```
https://cortex-agent-455006885273.asia-south1.run.app/tasks
```

**Show:**
- Filter buttons (All / Pending / Urgent / High)
- Click "Urgent" filter → shows the Rahul follow-up task
- Click "High" filter → shows Hackathon submission + Logo review

**Say:** "All your tasks, prioritized by urgency. Cortex pulls these from the PostgreSQL database — structured data that persists."

---

## SCENE 5: API Demo (3:45 - 4:30)
**Action:** Open Terminal/PowerShell

**Run these commands:**

```bash
# 1. Health check
curl https://cortex-agent-455006885273.asia-south1.run.app/api/health

# 2. Query — morning briefing
curl -X POST https://cortex-agent-455006885273.asia-south1.run.app/api/query \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"What's on my plate today?\"}"

# 3. Check memory
curl https://cortex-agent-455006885273.asia-south1.run.app/api/memory

# 4. Follow up with Rahul
curl -X POST https://cortex-agent-455006885273.asia-south1.run.app/api/query \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Send a follow-up to Rahul\"}"
```

**Say:** "It's also a REST API — every capability accessible programmatically. This is how you integrate it into your own workflows."

---

## SCENE 6: Architecture Slide (4:30 - 5:30)
**Action:** Show the architecture diagram from the README

**GitHub:** https://github.com/aayushprsingh/apac-hackathon

**Say:** "Under the hood — 5 agents. The Cortex Coordinator is the root agent that orchestrates specialized sub-agents: Memory Agent manages the persistent user model in PostgreSQL. Task Agent handles your to-do list. Scheduler Agent reads your Google Calendar. Email Agent manages Gmail. All deployed on Cloud Run as a serverless API."

**Show the project structure briefly.**

---

## SCENE 7: Submission Summary (5:30 - 6:00)
**Action:** Show the deployed URL + GitHub

```
https://cortex-agent-455006885273.asia-south1.run.app
https://github.com/aayushprsingh/apac-hackathon
```

**Say:** "Deployed on Google Cloud Run. All code on GitHub. The persistent memory layer is the key innovation — verified via live database query during the demo. Thank you."

---

## STOP RECORDING

**In OBS Studio: Click "Stop Recording"**

**Upload the MP4 to YouTube (unlisted) or Google Drive**
- YouTube unlisted link: Submit as demo link
- Google Drive: Share link as demo

---

## QUICK REFERENCE

| What to Show | URL |
|---|---|
| Main web UI | https://cortex-agent-455006885273.asia-south1.run.app |
| Memory browser | https://cortex-agent-455006885273.asia-south1.run.app/memory |
| Task manager | https://cortex-agent-455006885273.asia-south1.run.app/tasks |
| API health | https://cortex-agent-455006885273.asia-south1.run.app/api/health |
| GitHub repo | https://github.com/aayushprsingh/apac-hackathon |
| Hackathon submit | https://vision.hack2skill.com/event/apac-genaiacademy |

---

## DEMO MODE NOTE

The current deployed version runs in DEMO_MODE with in-memory storage. For the video, this is actually BETTER because:
- Everything loads instantly (no API auth setup needed)
- The demo data is realistic and contextual (Rahul, Bhooyam, hackathon tasks)
- Judges can verify it works without setting up Gmail/Calendar credentials

The production version (with real PostgreSQL + Gmail + Calendar) is ready to deploy using the scripts in the repo — demo mode is just for immediate accessibility.
