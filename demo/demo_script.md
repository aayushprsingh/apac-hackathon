# Cortex Demo Script
## Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

**Duration:** 5-7 minutes  
**Format:** Live demo + slides

---

## SETUP (Before Demo)

1. Open browser tabs:
   - Tab 1: Cortex web UI (http://localhost:8080 or Cloud Run URL)
   - Tab 2: PostgreSQL memory table (show live memory entries)
   - Tab 3: Gmail (show sent emails — prove it actually sent)
   - Tab 4: Google Calendar (show real events)

2. Database pre-loaded with seed data:
   - Rahul context (15% equity, ₹50L, 4 days overdue)
   - Current project: Bhooyam Ankuran Jal
   - 1 urgent task, 5 pending tasks

---

## SLIDE 1: Problem & Solution (30 sec)

**Slide content:**
```
THE PROBLEM:
Every AI tool is stateless.
Close the chat → It forgets everything.

THE SOLUTION: Cortex
A persistent multi-agent chief of staff
that remembers you across sessions.
```

**Narration:**
> "Every AI tool you've used — ChatGPT, Claude, Copilot — is stateless. After each conversation, it forgets who you are, what you're working on, what matters to you. Cortex solves this. It maintains a persistent memory model that updates after every interaction — and coordinates specialized agents to actually do work on your behalf."

---

## DEMO PART 1: Morning Briefing (2 min)

**Action:** Send this message in the web UI:
```
"What's on my plate today?"
```

**Expected Cortex response (assembled from all sources):**
```
☀️ Good morning! Here's your briefing for April 5, 2026:

📅 SCHEDULE:
• 11:00 AM — Design Review (1hr)
  Last discussed: Jal app UX flow
• 2:00 PM — Rahul: Investment Follow-up (30min)
  🔴 OVERDUE: 15% equity for ₹50L, waiting 4 days

📋 PENDING TASKS:
🔴 URGENT: Follow up with Rahul — by Apr 5 (TODAY!)
🟠 HIGH: Submit Hackathon Project — by Apr 8
🟠 HIGH: Review Bhooyam logo — by Apr 7

📧 ACTION ITEMS:
• Rahul sent email Apr 3 (unread) — "following up on equity terms"
• Invoice approval needed before 5pm

🧠 FROM YOUR MEMORY:
• Q1 goal: Launch Ankuran Jal MVP by April 15
• You committed to: "close Rahul investment this week"
```

**Narration:**
> "Notice what just happened. One message, and Cortex queried your Calendar, Tasks, Emails, AND Memory — all simultaneously, assembled into one coherent briefing. But the key differentiator is here — 'Rahul is 4 days overdue' — that's from the persistent memory layer. It learned this from our previous conversation. Let me prove it."

---

## DEMO PART 2: Memory Verification (1 min)

**Action:** Open the memory page in the web UI (or show database query)

**Show the `rahul_context` entry:**
```
key: "rahul_context"
value: {
  "name": "Rahul Sharma",
  "topic": "15% equity for ₹50L",
  "last_contact": "2026-04-03",
  "status": "waiting_on_rahul",
  "notes": "3-day deadline passed, now overdue"
}
confidence: 0.95, source: "chat"
updated_at: April 2, 2026
```

**Narration:**
> "This is the actual memory stored in PostgreSQL. This wasn't in today's calendar or emails — it was stored from a previous conversation. Cortex learned that I was waiting on Rahul, and surfaced it proactively today. THIS is why Cortex is different from every other AI tool."

---

## DEMO PART 3: Multi-Step Email Workflow (2 min)

**Action:** Send:
```
"Send a follow-up to Rahul about the investment terms"
```

**Cortex response (checkpoint — draft before sending):**
```
✏️ Draft email ready for your review:

To: rahul@email.com
Subject: Re: Investment Terms Discussion

Hi Rahul,

Following up from our conversation about the 15% equity 
proposal for ₹50L.

You mentioned you'd revert within 3 days — it's been 
4 days now. Is there an update on the legal review?

Let me know if you need anything from our side to move 
this forward.

Best, Aayush

---
Reply "send", "yes", or "go ahead" to send this email.
```

**Narration:**
> "Cortex didn't just send an email — it drafted one using BOTH the memory (15% equity, ₹50L, 3-day deadline) AND the previous email thread. Now it's showing me the draft and waiting for approval. This is the checkpoint pattern. Say 'send' to confirm."

**Action:** Type `send` in the chat

**Cortex response:**
```
✅ Email sent successfully!
🧠 Memory updated: Follow-up sent to Rahul on April 5
📋 Task logged: Follow up with Rahul — COMPLETED
```

**Show sent email in Gmail tab**

---

## SLIDE 2: Architecture (30 sec)

**Show architecture diagram**

```
┌─────────────────────────────────────────┐
│         CORTEX COORDINATOR              │
│   (Root LlmAgent — orchestrator)         │
└───────────────┬─────────────────────────┘
        ┌───────┼───────┬────────┐
        ▼       ▼       ▼        ▼
   ┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐
   │Memory  │ │Task  │ │Sched-│ │Email │
   │Agent   │ │Agent │ │uler  │ │Agent │
   └────┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
        │        │        │        │
        └────────┴───┬────┴────────┘
                    ▼
         PostgreSQL (Cloud SQL)
         user_model | tasks | projects
```

**Narration:**
> "Cortex is built on Google ADK — 5 agents in total. The Coordinator agent orchestrates specialized sub-agents, each responsible for one domain. They all share data through PostgreSQL. The key is the Memory Agent — it's the persistent layer that makes Cortex different."

---

## SLIDE 3: Submission Summary (30 sec)

```
PROJECT: Cortex
TEAM SIZE: Individual
TRACK: Cohort 1 Hackathon (Multi-Agent AI System)

WHAT WE BUILT:
✅ Primary root agent + 4 sub-agents
✅ Persistent memory model (PostgreSQL)
✅ Gmail API integration (read + send)
✅ Google Calendar API integration
✅ Multi-step workflow with checkpoints
✅ REST API deployed on Cloud Run

TECH STACK:
Google ADK · Gemini 2.5 Flash · PostgreSQL
Gmail API · Calendar API · Flask · Cloud Run

DEPLOYED: [Cloud Run URL]
REPO: [GitHub URL]
```

---

## KEY DEMO MOMENTS (for judges)

1. **"It remembered from yesterday"** — Memory table shown live, matches context from prior sessions
2. **The email is REAL** — Actually sent to Rahul, judges can see it
3. **One message → multiple agents** — Coordinator queries 4 sources simultaneously
4. **Checkpoint pattern** — Draft shown before sending (responsible AI)

---

## TROUBLESHOOTING

**Cortex doesn't respond:**
- Check if Flask app is running: `curl http://localhost:8080/api/health`
- Check database connection: `psql $DB_URL -c "SELECT 1"`

**Gmail/Calendar tools fail:**
- Verify OAuth credentials: `python tools/authenticate.py --test`
- Check API is enabled: `gcloud services list --enabled | grep gmail`

**Memory shows empty:**
- Run seed data: `psql $DB_URL < db/seed.sql`
- Check DB_HOST in .env matches Cloud SQL IP

---

_Last updated: 2026-04-05_
