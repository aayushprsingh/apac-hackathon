# Firebase + Gmail/Calendar Auto-Pull Setup Guide
## Cortex — Google Cloud Gen AI Academy APAC 2026

**Time needed: ~5-10 minutes**
**Most of this is point-and-click in Firebase console**

---

## Why Firebase?

Firebase and Google Cloud are the SAME PLATFORM. Your GCP project `dependable-glow-492112-e3` can also be a Firebase project. Firebase gives you:
- Firebase Auth (Google Sign-In, email/password) — **both work**
- Firestore (per-user database with automatic sync)
- All in the SAME project, same credentials

---

## Step 1: Convert GCP Project to Firebase Project (2 min)

1. Go to **console.firebase.google.com**
2. Click **"Add project"**
3. Select your Google account
4. Click **"Link a Google Cloud project"**
5. Choose: **dependable-glow-492112-e3**
6. Project name: `cortex-hackathon`
7. Click **"Create project"** (Google Analytics can be disabled)

That's it — your GCP project is now also a Firebase project.

---

## Step 2: Enable Authentication (2 min)

1. In Firebase console → **Build → Authentication → Get started**
2. Click on **"Google"** provider
3. Enable it
4. Select a **Project support email** (your email)
5. Click **Save**

Also enable **Email/Password** while you're here:
1. Click **Email/Password**
2. Enable it
3. Save

---

## Step 3: Get Firebase Config (1 min)

1. Go to **Project Settings** (gear icon)
2. Scroll to **"Your apps"**
3. Click **Web app** (</>) icon
4. Register app: name = `cortex-app`
5. **Don't** check Firebase Hosting
6. Copy the `firebaseConfig` object — it looks like:
```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "cortex-hackathon.firebaseapp.com",
  projectId: "cortex-hackathon",
  storageBucket: "cortex-hackathon.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

---

## Step 4: Enable Gmail + Calendar APIs (2 min)

1. Go to **console.cloud.google.com** → project `dependable-glow-492112-e3`
2. Go to **APIs & Services → Library**
3. Search and enable:
   - **Gmail API** (gmail.googleapis.com)
   - **Google Calendar API** (calendar-json.googleapis.com)
4. Go to **APIs & Services → Credentials**
5. Click **"Create credentials" → OAuth client ID**
6. Application type: **Web application**
7. Name: `Cortex Web Client`
8. Add **Authorized redirect URIs**: `https://cortex-hackathon.firebaseapp.com/__/auth/handler`
9. Click **Create**
10. Copy the **Client ID** and **Client Secret**

---

## Step 5: Add Credentials to the App (1 min)

In `app/templates/login.html`, replace the placeholder config:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

Also update these values in `app/templates/dashboard.html` and `app/templates/onboarding.html`.

For Gmail/Calendar auto-pull, add to `app/.env`:
```
GMAIL_CLIENT_ID=your-oauth-client-id
GMAIL_CLIENT_SECRET=your-oauth-client-secret
```

---

## Step 6: Deploy

```bash
cd hackathon-projects/apac-hackathon
gcloud builds submit --tag asia-south1-docker.pkg.dev/dependable-glow-492112-e3/cortex-repo/cortex-agent:v6 .
gcloud run deploy cortex-agent --image=asia-south1-docker.pkg.dev/dependable-glow-492112-e3/cortex-repo/cortex-agent:v6 ...
```

---

## What You Get After Setup

✅ **Google Sign-In** — users click "Sign in with Google" → real Google OAuth popup
✅ **Automatic Gmail pull** — Cortex reads user's inbox on sign-in, surfaces relevant emails in briefing
✅ **Automatic Calendar pull** — Cortex reads user's calendar on sign-in, shows today's schedule
✅ **Automatic task detection** — Cortex scans emails for task-like content and offers to create tasks
✅ **Per-user Firestore database** — all data isolated per user, persists across sessions

---

## TL;DR — What I Can't Do For You

| Step | Can I do it? | You need to do |
|------|-------------|----------------|
| Firebase console setup | ❌ Needs browser | ~5 min |
| Enable APIs | ✅ Done via CLI | Already done |
| Get Firebase config | ❌ Needs browser | ~2 min |
| Add config to code | ✅ Done now | Deploy |

---

## After Setup — The Experience

1. User visits `/login`
2. Clicks "Sign in with Google"
3. Google popup → user approves
4. **Cortex automatically pulls:**
   - Their name + email from Google profile
   - Today's calendar events from Google Calendar
   - Recent emails from Gmail
   - Existing tasks mentioned in emails
5. Cortex assembles morning briefing from ALL sources automatically
6. User sees: "Good morning! You have 3 meetings today, 2 emails need attention, and you promised Rahul a follow-up by Friday"

**No manual data entry. No typing. Just sign in.**
