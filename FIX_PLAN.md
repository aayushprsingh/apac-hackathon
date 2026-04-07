# Cortex — Bug Fix & Feature Plan
**Priority order. Deadline: April 8, 2026.**

---

## BUG 1: Email field — "auto-detected" is readonly, can't type
**File:** `app/templates/onboarding.html`
**Fix:** Remove `readonly` from `userEmail` input. In demo/non-Firebase mode, it's just a regular editable field. Label should say "Your email" not "auto-detected".

## BUG 2: "Complete Setup" → 401 Authentication Required
**File:** `app/app.py`
**Root cause:** `DEMO_TOKEN` is per-process. When Cloud Run has multiple processes (or after restart), the demo session isn't shared. `get_current_user()` returns None → 401.
**Fix:** 
1. Add `DEMO_MODE` bypass in `require_auth` decorator — if `DEMO_MODE=True` and `DEMO_TOKEN` is set, accept demo token without checking `_sessions`
2. Better: persist demo sessions to SQLite (already done for regular sessions), just ensure demo session also gets saved

## BUG 3: "Skip — I'll configure later" not working
**File:** `app/templates/onboarding.html`
**Root cause:** `onclick="finishOnboarding()"` on skip link tries to POST to `/api/auth/onboarding` — same auth issue as Bug 2.
**Fix:** Skip link should just redirect to `/dashboard` directly — no API call needed for demo users.

## BUG 4: Auto-pull Gmail/Calendar — not happening at all
**File:** `app/app.py` + `app/firebase_auth.py`
**Root cause:** Firebase is disabled. `firebase_auth.py` is a stub. No Gmail/Calendar OAuth.
**Fix (pragmatic for hackathon):** 
1. Onboarding Step 1 already collects email — use it for briefing
2. Add a "Connect Gmail" button in onboarding that initiates Google OAuth (simple redirect flow, no Firebase needed)
3. After OAuth, store access tokens in SQLite, auto-pull emails + calendar on sign-in
4. Show "demo data" when not connected, real data when connected
5. This satisfies "interacts with Gmail and Calendar APIs"

## BUG 5: Target audience — only working professionals
**File:** `app/templates/onboarding.html` + `app/templates/dashboard.html`
**Fix:** Change all references from "working professionals" to "anyone who wants to stay organized — students, creators, founders, professionals"

---

## Execution Order

### Phase 1: Critical Bugs (must fix for demo to work)
1. Fix `require_auth` in app.py — demo bypass
2. Fix email field in onboarding.html
3. Fix skip button in onboarding.html
4. Update target audience text

### Phase 2: Gmail/Calendar Integration
5. Add Google OAuth flow (simple, no Firebase)
6. Auto-pull emails + calendar after OAuth
7. Show connected/disconnected state in UI

### Phase 3: Polish
8. Better demo personas (student, founder, researcher)
9. Improve briefing quality with user data
10. Test full flow end-to-end

---

## Hackathon Requirements Check
From problem statement: "Build a production-aware AI capability that improves a user interaction or internal workflow"
- ✅ Multi-agent (Cortex coordinator + 4 sub-agents)
- ✅ Connects to real-world data (Gmail, Calendar — once OAuth wired)
- ✅ Multi-step workflow with checkpoint (email draft → user approve)
- ✅ ADK on Cloud Run
- Need to: Wire Gmail/Calendar OAuth properly, show real data pull
